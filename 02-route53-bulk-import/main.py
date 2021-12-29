import codecs
import csv
import logging
import time

import boto3

from Route53Request import Route53Request
from RequestException import RequestException

route53 = boto3.client("route53")
s3 = boto3.client("s3")


def read_csv_input(bucket, key):
    """
    Reads a csv file from the given S3 bucket and key and returns a
    DictReader object

    Parameters:
    - bucket: str - the name of the S3 bucket from which to read csv file
    - key: str - the key name or filename of the csv file to read

    Returns:
    - DictReader - the csv file reader object that maps the data into
                    a dictionary
    """
    try:
        csv_file = s3.get_object(Bucket=bucket, Key=key)
        csv_data = csv_file['Body'].read().split(b'\n')
        csv_data_dict = csv.DictReader(codecs.iterdecode(csv_data,
                                                         'utf-8-sig'))

        return csv_data_dict
    except Exception as e:
        logging.error(str(e))
        raise RequestException(message='Failed to read CSV file from S3',
                               error_data=key)

def group_data_by_domain_name(csv_data):
    """
    Reads each row from the input CSV and groups them by domain name.

    Parameters:
    - csv_data: DictReader-CSV data, each row is one record change request

    Returns:
    - dict - key-value pairs of domain names and list of Route53Requests
    """
    changes_dict = {}

    for i, row in enumerate(csv_data):
        request_info = Route53Request(action=row['action'],
                                      domain_name=row['domain_name'],
                                      recordset_name=row['record_name'],
                                      recordset_value=row['value'],
                                      recordset_type=row['record_type'])

        if request_info.is_valid_action() == False:
            raise RequestException(message='Invalid request action',
                                   index=i + 1,
                                   error_data=request_info.action)

        if request_info.is_valid_record_type() == False:
            raise RequestException(message='Record type is not recognised',
                                   index=i + 1,
                                   error_data=request_info.recordset_type)

        if request_info.domain_name not in changes_dict.keys():
            changes_dict[request_info.domain_name] = [request_info]
        else:
            changes_dict[request_info.domain_name].append(request_info)

    return changes_dict

def get_hosted_zone_id(domain_name, zone_type):
    """
    Retrieves the hosted zone ID of a given domain name from Route 53

    Parameters:
    - domain_name: str - the domain name to look for in Route 53
    - zone_type: str - public or private; indicates whether the domain name
                        is accessible via the internet (public) or only
                        within a VPC (private)

    Returns:
    - str - the zone ID of the domain name in Route 53
    """
    response_zones = None
    zone_id = None

    try:
        response_zones = route53.list_hosted_zones_by_name(
            DNSName=domain_name,
            MaxItems="2"
        )

    except Exception as e:
        logging.error(str(e))
        raise RequestException(
            message='Could not perform list operation from Route 53',
            error_data=domain_name)

    for zone in response_zones['HostedZones']:
        zone_name = zone['Name']
        response_zone_type = ('private'
                              if zone['Config']['PrivateZone'] is True
                              else 'public')

        if domain_name + '.' == zone_name and zone_type == response_zone_type:
            if zone_id is not None:
                raise RequestException(
                    message='Multiple hosted zones with the same \
                             name {0} were found'.format(domain_name))

            zone_id = zone['Id'].partition("hostedzone/")[2]

    if zone_id is None:
        raise RequestException(('The hosted zone {0} does not exist'
                                .format(domain_name)))

    return zone_id


def commit_changes(domain_name, zone_id, action_requests):
    """
    Pushes all DNS record changes associated to a domain name (represented
    by zone_id) by bulk through the ChangeBatch parameter
    of change_resource_record_sets() API

    Parameters:
    - domain_name: str - the name of the hosted zone in which the DNS record
                         changes will be made
    - zone_id: str - the zone id of the hosted zone in which the DNS record
                     changes will be made
    - action_requests: list[Route53Request] - a list of objects of type
                        Route53Request. Each Route53Request is one action
                        to perform on a DNS record of the specified domain.

    Return:
    - response_msg: str - a unique identifier returned by a successful
                          Route 53 API call
    """
    action_json = []

    for action_request in action_requests:
        action_json.append(action_request.generate_change_recordset_json())

    try:
        response = route53.change_resource_record_sets(
            HostedZoneId=zone_id,
            ChangeBatch={
                'Changes': action_json
            }
        )

        # Wait 1 second for bulk updates to complete
        time.sleep(1)

        response_msg = response['ChangeInfo']['Id']

        return response_msg

    except Exception as e:
        logging.error(str(e))
        raise RequestException(message="Failed to commit changes to Route 53",
                               error_data=domain_name)


def process_changes(changes_dict):
    """
    Iterates through each unique domain name from the input file and
    processes all associated requests by bulk by calling commit_changes()
    to push the request details to Route 53.

    Parameters:
    - changes_dict: dict - a dictionary of unique domain names as keys and
                           a list of all requests associated to the domain
                           name as the values

    Returns:
    - response_msgs: list - a list of successful Route 53 API response
                            reference numbers
    """
    response_msgs = []

    for domain_name in changes_dict.keys():
        action_requests = changes_dict[domain_name]

        zone_id = get_hosted_zone_id(domain_name, action_requests[0].zone_type)

        response_msgs.append(commit_changes(domain_name,
                                            zone_id,
                                            action_requests))

    return response_msgs


def handler(event, context):
    """
    Function entrypoint - set Lambda function runtime settings to Python 3.7
    and main.handler as the handler.
    """
    try:
        bucket = event['file_name']['bucket']['name']
        key = event['file_name']['object']['key']

        csv_data = read_csv_input(bucket, key)
        changes_dict = group_data_by_domain_name(csv_data)
        response_msgs = process_changes(changes_dict)

        APIresponse = {
            "number": event['number'],
            "state": "Successfully committed changes to Route53",
            "message": ','.join(response_msgs),
        }

    except RequestException as req_exc:
        logging.error(str(req_exc))

        APIresponse = {
            "number": event['number'],
            "state": "Error",
            "message": req_exc.get_msg_data()
        }
    finally:
        return APIresponse
