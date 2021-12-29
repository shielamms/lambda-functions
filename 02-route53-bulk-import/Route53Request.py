class Route53Request:
    def __init__(self,
                 action,
                 domain_name,
                 zone_type='public',
                 recordset_name=None,
                 recordset_value=None,
                 recordset_type=None,
                 ttl=300):
        self.action = action
        self.domain_name = domain_name.lower()
        self.zone_type = zone_type
        self.recordset_name = recordset_name
        self.recordset_value = recordset_value
        self.recordset_type = recordset_type
        self.ttl = ttl

        if self.recordset_type == 'TXT':
            self.add_quotes_to_txt_values()

    def is_valid_action(self):
        if self.action not in ['UPSERT', 'DELETE']:
            return False
        return True

    def is_valid_record_type(self):
        if (self.recordset_type
            not in ['MX', 'PTR', 'A', 'CNAME', 'SRV', 'TXT', 'NS', 'AAAA']):
                return False
        return True

    def add_quotes_to_txt_values(self):
        for i, val in enumerate(self.recordset_value):
            self.recordset_value[i] = "\"" + val + "\""

    def generate_change_recordset_json(self):
        """
        Generates the JSON containing the request details required by the
        change_resource_record_sets() API
        """
        return {
            'Action': self.action,
            'ResourceRecordSet': {
                'Name': self.recordset_name,
                'Type': self.recordset_type,
                'TTL': self.ttl,
                'ResourceRecords': [
                    {
                        'Value': self.recordset_value
                    }
                ]
            }
        }
