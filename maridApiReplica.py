import string

from flask import Flask, Response, request
import boto3, json, uuid, random

app = Flask(__name__)

sqs_client = boto3.client("sqs")
sts_client = boto3.client("sts")
N = 2000
TOKEN_KEYS = [
    "AccessKeyId",
    "SecretAccessKey",
    "SessionToken",
    "Expired"
]

policy = json.dumps({
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "VisualEditor0",
            "Effect": "Allow",
            "Action": [
                "sqs:DeleteMessage",
                "sqs:ReceiveMessage"

            ],
            "Resource": "arn:aws:sqs:eu-west-1:*:*"
        }
    ]
})


@app.route('/queue-generator', methods=['POST'])
def hello_world():
    req_data = request.get_json()
    integration_id = req_data["apiKey"]
    try:
        response = sqs_client.create_queue(QueueName=integration_id)
    except Exception as e:
        return Response(json.dumps({"_error": str(e)}), status=400, mimetype="application/json")
    return Response(json.dumps({"queue_name": response['QueueUrl']}), status=200)


def _random_entry_generator():
    entry = {}
    entry['Id'] = str(uuid.uuid4())
    entry['MessageBody'] = ''.join(random.choices(string.ascii_uppercase + string.digits, k=N))
    return entry


'''
{
    'Id': 'string', #required
    'MessageBody': 'string', #required
    'DelaySeconds': 123,
    'MessageAttributes': {
        'string': {
            'StringValue': 'string',
            'BinaryValue': b'bytes',
            'StringListValues': [
                'string',
            ],
            'BinaryListValues': [
                b'bytes',
            ],
            'DataType': 'string'
        }
    },
    'MessageDeduplicationId': 'string',
    'MessageGroupId': 'string'
}
'''


@app.route('/message-publisher', methods=['POST'])
def message_publisher():
    req_data = request.get_json()
    que_url = req_data['queueUrl']
    entries = []
    for _ in range(random.randint(1, 10)):
        entries.append(_random_entry_generator())
    try:
        response = sqs_client.send_message_batch(
            QueueUrl=que_url,
            Entries=entries
        )
    except Exception as e:
        return Response(str(e), status=400)
    return Response(json.dumps(entries), status=200, mimetype="application/json")


def generate_token_response(credentials):
    res = {}
    for key in TOKEN_KEYS:
        res[key] = credentials[key]
    return res


@app.route('/sts-generator', methods=['POST'])
def sts_generator():
    req_data = request.get_json()
    que_url = req_data['apiKey']
    response = sts_client.get_federation_token(
        Name='marid-test',
        Policy=policy,
        DurationSeconds=3600
    )
    res = generate_token_response(response["Credentials"])
    return Response(json.dumps(res), status=200, mimetype='application/json')


@app.route('/dummy', methods=['POST'])
def dummy():
    req_data = request.get_json()
    alertInfo = req_data['alertInfo']
    print (alertInfo)
    configs = req_data['config']
    print (configs)
    return Response(status=200, mimetype="application/json")


if __name__ == '__main__':
    app.run()
