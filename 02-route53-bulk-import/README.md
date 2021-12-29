# Route53 Bulk Import

This project is an AWS Lambda function in Python that can import a batch of Route53 requests from a CSV file in S3. The CSV file contains the list of actions, domain names, record set names, and other record attributes to add/update/delete in Route53.

The test data sample-bulk-import.csv is provided. Upload the file in your S3 bucket and take note of the bucket name and key.

The input payload to the Lambda function looks like this, replacing **bucket-name** and **key-name** with the values from your S3 bucket. **request-number** is an arbitrary value provided by the requesting application to keep a reference on API calls.
```json
{
  "number": "request-number",
  "file_name": {
    "bucket": {
      "name": "bucket-name"
    },
    "object": {
      "key": "key-name"
    }
  }
}
```
