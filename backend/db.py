import boto3

dynamodb = boto3.resource(
    'dynamodb',
    endpoint_url='http://localhost:8001',  # ローカルならこれ（AWS の場合は消す）
    region_name='ap-northeast-1',
    aws_access_key_id='fakeMyKeyId',       # ローカルならダミーでOK
    aws_secret_access_key='fakeSecretAccessKey'
)

qa_item_table = dynamodb.Table('QAitem')
qa_info_table = dynamodb.Table('QAinfo')
qa_result_table = dynamodb.Table('QAresult')