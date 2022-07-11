###############################################################################
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#
###############################################################################

import json
import logging
from pathlib import Path
from typing import Any, Union
from urllib.parse import urlparse

from minio import Minio
from minio.notificationconfig import NotificationConfig, QueueConfig

from wis2box.storage.base import PolicyTypes, StorageBase

LOGGER = logging.getLogger(__name__)


# default policies

def readonly_policy(name):
    return {
        'Version': '2012-10-17',
        'Statement': [{
            'Effect': 'Allow',
            'Principal': {'AWS': '*'},
            'Action': ['s3:GetBucketLocation', 's3:ListBucket'],
            'Resource': f'arn:aws:s3:::{name}',
        }, {
            'Effect': 'Allow',
            'Principal': {'AWS': '*'},
            'Action': 's3:GetObject',
            'Resource': f'arn:aws:s3:::{name}/*',
        }]
    }


def readwrite_policy(name):
    return {
        'Version': '2012-10-17',
        'Statement': [{
            'Effect': 'Allow',
            'Principal': {'AWS': '*'},
            'Action': [
                's3:GetBucketLocation',
                's3:ListBucket',
                's3:ListBucketMultipartUploads',
            ],
            'Resource': f'arn:aws:s3:::{name}',
        }, {
            'Effect': 'Allow',
            'Principal': {'AWS': '*'},
            'Action': [
                's3:GetObject',
                's3:PutObject',
                's3:DeleteObject',
                's3:ListMultipartUploadParts',
                's3:AbortMultipartUpload',
            ],
            'Resource': f'arn:aws:s3:::{name}/*',
        }]
    }


class MinioStorage(StorageBase):
    """Abstract storage manager"""
    def __init__(self, storage_type, source: str,
                 name: str = None, auth: dict = {},
                 policy: Union[PolicyTypes, None] = None) -> None:

        super().__init__('MinIO', source, name, auth, policy)

        is_secure = False

        urlparsed = urlparse(self.source)

        if self.source.startswith('https://'):
            is_secure = True

        self.client = Minio(endpoint=urlparsed.netloc,
                            access_key=self.auth['username'],
                            secret_key=self.auth['password'],
                            secure=is_secure)

    def setup(self):
        LOGGER.debug(f'Creating buckets at MinIO endpoint {self.source}')
        self.create_bucket(bucket_policy=self.policy)

    def set_policy(self, bucket_policy: PolicyTypes = 'private'):
        LOGGER.debug(f'Set bucket_policy={bucket_policy} on {self.name}')
        if bucket_policy == 'readonly':
            self.client.set_bucket_policy(
                self.name, json.dumps(readonly_policy(self.name)))
        elif bucket_policy == 'readwrite':
            self.client.set_bucket_policy(
                self.name, json.dumps(readwrite_policy(self.name)))
        elif bucket_policy == 'private':
            self.client.delete_bucket_policy(self.name)
        else:
            LOGGER.warning(f'bucket_policy={bucket_policy} unknown')

    def create_bucket(self, bucket_policy: PolicyTypes = 'private'):
        # create bucket if not exist
        found = self.client.bucket_exists(self.name)
        if not found:
            self.client.make_bucket(self.name)
        else:
            LOGGER.info(f'Bucket {self.name} already exists')
        self.set_policy(bucket_policy)
        # add notifications to be sent to local-broker
        config = NotificationConfig(
            queue_config_list=[
                QueueConfig(
                    'arn:minio:sqs::WIS2BOX:mqtt',
                    ['s3:ObjectCreated:*'],
                    config_id='1'
                )
            ]
        )
        LOGGER.debug(f'Adding notification config {config}')
        self.client.set_bucket_notification(self.name, config)

    def get(self, identifier: str) -> Any:

        LOGGER.debug(f'Getting object {identifier} from bucket={self.name}')
        # Get data of an object.
        try:
            response = self.client.get_object(
                self.name, object_name=identifier)
            data = response.data
        except Exception as e:
            LOGGER.error(e)
            raise e
        finally:
            response.close()
            response.release_conn()

        return data

    def put(self, filepath: Path, identifier: str) -> bool:

        LOGGER.debug(f'Putting file {filepath} as object={identifier}')
        self.client.fput_object(bucket_name=self.name, object_name=identifier,
                                file_path=filepath)

        return True

    def put_bytes(self, data: bytes, identifier: str) -> bool:

        LOGGER.debug(f'Putting data as object={identifier}')
        self.client.put_object(bucket_name=self.name, object_name=identifier,
                               data=data, length=-1, part_size=10*1024*1024)

        return True

    def delete(self, identifier: str) -> bool:

        LOGGER.debug(f'Deleting object {identifier}')
        self.client.delete_object(Bucket=self.name, Key=identifier)

        return True

    def __repr__(self):
        return f'<MinioStorage ({self.source})>'
