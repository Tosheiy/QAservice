import boto3

dynamodb = boto3.resource('dynamodb')

qa_item_table = dynamodb.Table('QAitem')
qa_info_table = dynamodb.Table('QAinfo')
qa_result_table = dynamodb.Table('QAresult')