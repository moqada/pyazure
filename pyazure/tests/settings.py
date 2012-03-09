import test_settings

AZURE_FILES = {
    'account_name': test_settings.AZURE_ACCOUNT_NAME,
    'key': test_settings.AZURE_ACCOUNT_KEY,
    'container_name': 'test-container',
    'base_url': 'https://%s.blob.core.windows.net/test-container/' % test_settings.AZURE_ACCOUNT_NAME,
}

PRIVATE_AZURE_FILES = {
    'account_name': test_settings.AZURE_ACCOUNT_NAME,
    'key': test_settings.AZURE_ACCOUNT_KEY,
    'container_name': 'test-private-container',
    'base_url': 'https://%s.blob.core.windows.net/test-private-container/' % test_settings.AZURE_ACCOUNT_NAME,
    'is_private': True,
}
