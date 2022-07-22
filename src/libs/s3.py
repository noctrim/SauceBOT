import boto3
import os

AWS_KEY = os.environ["AWS_KEY"]
AWS_SECRET_KEY = os.environ["AWS_SECRET_KEY"]

session = boto3.Session(aws_access_key_id=AWS_KEY, aws_secret_access_key=AWS_SECRET_KEY)
s3 = session.resource('s3')
s3_bucket = s3.Bucket("noctrimphotos")
SENT_PHOTOS = set()


def get_all_relevant_photos():
    """
    Gets all sauce photos

    :return: list of photos
    """
    return [f.key for f in s3_bucket.objects.all() if not f.key.endswith("/") and "Sauce" in f.key]


def download_file(name, output_path):
    """
    Downloads a given file name from sauce bucket

    :param name: name of file to download
    :param output_path: location to save file
    """
    s3_bucket.download_file(name, output_path)
