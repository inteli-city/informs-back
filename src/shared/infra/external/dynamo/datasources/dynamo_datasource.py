import json
from decimal import Decimal

import boto3


class DynamoDatasource:
    """
    Docs:
    - https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb.html#DynamoDB.Table
    """
    dynamo_table: boto3.resource
    partition_key: str
    sort_key: str
    gsi_partition_key: str
    gsi_sort_key: str

    def __init__(self, dynamo_table_name: str, partition_key: str, region: str, gsi_partition_key: str = None, gsi_sort_key: str = None,
                 endpoint_url: str = None, sort_key: str = None):

        s = boto3.Session(region_name=region)
        self.dynamo_resource = s.resource('dynamodb', endpoint_url=endpoint_url)
        self.endpoint_url = endpoint_url
        self.dynamo_table = self.dynamo_resource.Table(dynamo_table_name)
        self.partition_key = partition_key
        self.sort_key = sort_key
        self.gsi_partition_key = gsi_partition_key
        self.gsi_sort_key = gsi_sort_key

    @staticmethod
    def _parse_float_to_decimal(item):
        """
        Parse float to Decimal
        @param item: dict with the keys (Partition and Sort) and data to insert
        """
        def _json_default(value):
            if isinstance(value, Decimal):
                return float(value)
            raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")

        item_parsed = json.loads(json.dumps(item, default=_json_default), parse_float=Decimal)
        return item_parsed

    def put_item(self, item: dict, partition_key: str, sort_key: str = None, **kwargs):
        """
        Insert a new item into the table or hard update an existing one.
        Ref: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb.html#DynamoDB.Table.put_item
        @param item: dict with the keys (Partition and Sort) and data to insert
        @param partition_key: string with the partition key
        @param sort_key: string with the sort key (optional)
        @return: dict with the response from DynamoDB
        """

        is_decimal = kwargs.pop("is_decimal", False)
        item = DynamoDatasource._parse_float_to_decimal(item) if not is_decimal else item

        item[self.partition_key] = partition_key
        if sort_key:
            item[self.sort_key] = sort_key

        return self.dynamo_table.put_item(Item=item, **kwargs)

    def get_item(self, partition_key: str, sort_key: str = None):
        """
        Get an item from the table from its keys (Partition and Sort).
        @param partition_key: string with the partition key
        @param sort_key: string with the sort key (optional)
        @return: dict with the response from DynamoDB
        """
        key = {self.partition_key: partition_key, self.sort_key: sort_key if sort_key else None}
        key_without_none_values = {k: v for k, v in key.items() if v is not None}
        resp = self.dynamo_table.get_item(
            Key=key_without_none_values
        )
        return resp

    def hard_update_item(self, partition_key: str, sort_key: str, item: dict):
        """
        Hard update an item in the table (must have its keys - Partition and Sort).
        @param partition_key: string with the partition key
        @param sort_key: string with the sort key (optional)
        @param item: dict with data to insert
        @return: dict with the response from DynamoDB
        """

        item[self.partition_key] = partition_key

        if sort_key:
            item[self.sort_key] = sort_key

        resp = self.dynamo_table.put_item(Item=DynamoDatasource._parse_float_to_decimal(item))
        return resp

    def update_item(self, partition_key: str, sort_key: str, update_dict: dict, condition_expression=None):
        """
        Update an item in the table with its keys (Partition and Sort) and attributes to update
        If the attribute does not exist, it will be created. It won't change attributes not mentioned.
        @param key: dict with the keys (Partition and Sort)
        @param update_attributes: dict with the attributes to update
        @return: dict with the response from DynamoDB
        """

        update_dict = DynamoDatasource._parse_float_to_decimal(update_dict)
        data_key_value_pairs = list(update_dict.items())

        update_expression = "SET " + ", ".join([f"#attr{i} = :val{i}" for i in range(len(data_key_value_pairs))]) # SET attribute1=:value1, attribute2=:value2
        expression_attribute_names = {f"#attr{i}": data_key_value_pairs[i][0] for i in range(len(data_key_value_pairs))} # {"_attribute1": "attribute1", ":_attribute2": "attribute2"}
        expression_value_names = {f":val{i}": data_key_value_pairs[i][1] for i in range(len(data_key_value_pairs))} # {":value1": "value1", ":value2": "value2"}

        
        
        key = {self.partition_key: partition_key, self.sort_key: sort_key if sort_key else None}
        key_without_none_values = {k: v for k, v in key.items() if v is not None}
        kwargs = {
            "Key": key_without_none_values,
            "UpdateExpression": update_expression,
            "ExpressionAttributeNames": expression_attribute_names,
            "ExpressionAttributeValues": expression_value_names,
            "ReturnValues": "ALL_NEW",
        }
        if condition_expression is not None:
            kwargs["ConditionExpression"] = condition_expression

        resp = self.dynamo_table.update_item(**kwargs)
        
        return resp

    def delete_item(self, partition_key: str, sort_key: str = None):
        """
        Delete an item from the table from its keys (Partition and Sort).
        @param partition_key: string with the partition key
        @param sort_key: string with the sort key (optional)
        @return: dict with the response from DynamoDB
        """
        key = {self.partition_key: partition_key, self.sort_key: sort_key if sort_key else None}
        key_without_none_values = {k: v for k, v in key.items() if v is not None}
        resp = self.dynamo_table.delete_item(
            Key=key_without_none_values,
            ReturnValues='ALL_OLD'
        )
        return resp

    def scan_items(self, filter_expression, **kwargs):
        """
        Scan items from the table.
        @return: dict with the response from DynamoDB
        """

        resp = self.dynamo_table.scan(
            FilterExpression=filter_expression,
            **kwargs
        )
        return resp

    def query(self, key_condition_expression, **kwargs):
        """
        Query the table with the KeyConditionExpression.
        Example: KeyConditionExpression=Key('Partition').eq('partition') & Key('Sort').gte('sort')
        Obs: Key de boto3.dynamodb.conditions.Key
        Ref:https://boto3.amazonaws.com/v1/documentation/api/latest/reference/customizations/dynamodb.html#ref-dynamodb-conditions
        @param key_condition_expression: string with the KeyConditionExpression
        @return: dict with the response from DynamoDB
        """

        resp = self.dynamo_table.query(
            KeyConditionExpression=key_condition_expression,

            **kwargs
        )
        return resp

    def batch_write_items(self, items):
        """
        Write a list of items to the table. Each item must have the keys (Partition and Sort).
        @param items: list of dicts with the keys (Partition and Sort) and data to insert
        """

        with self.dynamo_table.batch_writer() as batch:
            for i in items:
                batch.put_item(Item=DynamoDatasource._parse_float_to_decimal(i))

    def batch_delete_items(self, keys):
        """
        Delete a list of items from the table. Each item must have only the keys (Partition and Sort).
        @param keys: list of dicts with the keys (Partition and Sort)
        Example: keys=[ {'Partition': 'partition1', 'Sort': 'sort2'}, {'Partition': 'partition1', 'Sort': 'sort2'} ]
        """

        with self.dynamo_table.batch_writer() as batch:
            for k in keys:
                batch.delete_item(Key=k)
                
    def batch_get_items(self, keys):
        """
        Get a list of items from the table. Each item must have only the keys (Partition and Sort).
        @param keys: list of dicts with the keys (Partition and Sort)
        Example: keys=[ {'Partition': {'S': 'partition1'}, 'Sort': {'S': 'sort2'}}, {'Partition': {'S': 'partition1'}, 'Sort': {'S': 'sort2'}}}}]
        """
        # pk':{'S':item},'sk': {'S':'ITEM'}}

        resp = self.dynamo_resource.batch_get_item(
                RequestItems={
                    self.dynamo_table.name: {
                        'Keys': keys
                    }
            }
        )
        return resp
    
    def transact_write_items(self, transact_items):
        """
        Perform a transactional write operation on multiple items in one or more tables.
        @param transact_items: list of dicts with the transactional write operations
        Example: transact_items=[
            {
                'Put': {
                    'TableName': 'YourTableName',
                    'Item': {
                        'Partition': {'S': 'partition1'},
                        'Sort': {'S': 'sort1'},
                        'Attribute1': {'S': 'value1'}
                    }
                }
            },
            {
                'Delete': {
                    'TableName': 'YourTableName',
                    'Key': {
                        'Partition': {'S': 'partition2'},
                        'Sort': {'S': 'sort2'}
                    }
                }
            }
        ]
        """

        resp = self.dynamo_resource.transact_write_items(
            TransactItems=transact_items
        )
        return resp
    
    def build_transaction_item_put(self, item: dict, partition_key: str, sort_key: str = None):
        """
        Build a transaction item for a Put operation.
        @param item: dict with the keys (Partition and Sort) and data to insert
        @param partition_key: string with the partition key
        @param sort_key: string with the sort key (optional)
        @return: dict with the transaction item for Put operation
        """
        from boto3.dynamodb.types import TypeSerializer
        
        item = DynamoDatasource._parse_float_to_decimal(item)

        item[self.partition_key] = partition_key
        if sort_key:
            item[self.sort_key] = sort_key

        # Serialize item with type descriptors for transact_write_items
        serializer = TypeSerializer()
        serialized_item = {k: serializer.serialize(v) for k, v in item.items()}

        transaction_item = {
            'Put': {
                'TableName': self.dynamo_table.name,
                'Item': serialized_item
            }
        }

        return transaction_item
    
    def build_transaction_item_delete(self, partition_key: str, sort_key: str = None):
        """
        Build a transaction item for a Delete operation.
        @param partition_key: string with the partition key
        @param sort_key: string with the sort key (optional)
        @return: dict with the transaction item for Delete operation
        """
        from boto3.dynamodb.types import TypeSerializer
        
        serializer = TypeSerializer()
        key = {self.partition_key: serializer.serialize(partition_key)}
        if sort_key:
            key[self.sort_key] = serializer.serialize(sort_key)

        transaction_item = {
            'Delete': {
                'TableName': self.dynamo_table.name,
                'Key': key
            }
        }

        return transaction_item
