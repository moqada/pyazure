def clear_storage(blob_storage, container_name):
    for blob in blob_storage.list_blobs(container_name):
        try:
            blob_storage.delete_blob(container_name, blob[0])
        except Exception, e:
            # Python 2.5 compatibility
            if e.code != 202:
                raise e

