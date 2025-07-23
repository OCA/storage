# Copyright 2025 Camptocamp SA (http://www.camptocamp.com).
# @author Simone Orsi <simone.orsi@camptocamp.com>

import logging

import boto3

_logger = logging.getLogger(__name__)

# Last update 2025-04-16
AWS_REGIONS = [
    ("af-south-1", "Af south 1"),
    ("ap-east-1", "Ap east 1"),
    ("ap-northeast-1", "Ap northeast 1"),
    ("ap-northeast-2", "Ap northeast 2"),
    ("ap-northeast-3", "Ap northeast 3"),
    ("ap-south-1", "Ap south 1"),
    ("ap-south-2", "Ap south 2"),
    ("ap-southeast-1", "Ap southeast 1"),
    ("ap-southeast-2", "Ap southeast 2"),
    ("ap-southeast-3", "Ap southeast 3"),
    ("ap-southeast-4", "Ap southeast 4"),
    ("ap-southeast-5", "Ap southeast 5"),
    ("ap-southeast-7", "Ap southeast 7"),
    ("ca-central-1", "Ca central 1"),
    ("ca-west-1", "Ca west 1"),
    ("eu-central-1", "Eu central 1"),
    ("eu-central-2", "Eu central 2"),
    ("eu-north-1", "Eu north 1"),
    ("eu-south-1", "Eu south 1"),
    ("eu-south-2", "Eu south 2"),
    ("eu-west-1", "Eu west 1"),
    ("eu-west-2", "Eu west 2"),
    ("eu-west-3", "Eu west 3"),
    ("il-central-1", "Il central 1"),
    ("me-central-1", "Me central 1"),
    ("me-south-1", "Me south 1"),
    ("mx-central-1", "Mx central 1"),
    ("sa-east-1", "Sa east 1"),
    ("us-east-1", "Us east 1"),
    ("us-east-2", "Us east 2"),
    ("us-west-1", "Us west 1"),
    ("us-west-2", "Us west 2"),
]


def _load_aws_regions():
    _logger.info("Loading available AWS regions")
    session = boto3.session.Session()
    return [
        (region, region.replace("-", " ").capitalize())
        for region in session.get_available_regions("s3")
    ]


if __name__ == "__main__":
    # AWS regions won't change that often,
    # fine to retrieve them only when you need to update them.
    #
    # run `python storage_backend_s3/regions.py` to update the list
    # and update the AWS_REGIONS variable above.
    print(_load_aws_regions())  # pylint: disable=print-used
