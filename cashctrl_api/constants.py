CATEGORY_COLUMNS = {
        'id': 'int',
        'name': 'string[python]',
        'path': 'string[python]',
        'text': 'string[python]',
        'parentId': 'Int64',
        'created': 'datetime64[ns, Europe/Berlin]',
        'createdBy': 'string[python]',
        'lastUpdated': 'datetime64[ns, Europe/Berlin]',
        'lastUpdatedBy': 'string[python]',
        'cls': 'string[python]',
        'leaf': 'bool',
        'disableAdd': 'bool',
        'isSystem': 'bool',
}
FILE_COLUMNS = {
        'id': 'int',
        'name': 'string[python]',
        'path': 'string[python]',
        'description': 'string[python]',
        'notes': 'string[python]',
        'size': 'int',
        'mimeType': 'string[python]',
        'isAttached': 'bool',
        'attachedCount': 'int',
        'categoryId': 'Int64',
        'categoryName': 'string[python]',
        'created': 'datetime64[ns, Europe/Berlin]',
        'createdBy': 'string[python]',
        'lastUpdated': 'datetime64[ns, Europe/Berlin]',
        'lastUpdatedBy': 'string[python]',
        'dateArchived': 'datetime64[ns, Europe/Berlin]',
}
TAX_COLUMNS = {
        'id': 'int',
        'created': 'datetime64[ns, Europe/Berlin]',
        'createdBy': 'string[python]',
        'lastUpdated': 'datetime64[ns, Europe/Berlin]',
        'lastUpdatedBy': 'string[python]',
        'accountId': 'int',
        'name': 'string[python]',
        'documentName': 'string[python]',
        'accountDisplay': 'string[python]',
        'calcType': 'string[python]',
        'percentage': 'float64',
        'percentageFlat': 'Int64', # how should deal with the OR types
        'listCls': 'string[python]',
        'value': 'string[python]',
        'isInactive': 'bool',
        'isPreTax': 'bool',
        'isFlat': 'bool',
        'isGrossCalcType': 'bool',
}
ACCOUNT_COLUMNS = {
        'id': 'int',
        'created': 'datetime64[ns, Europe/Berlin]',
        'createdBy': 'string[python]',
        'lastUpdated': 'datetime64[ns, Europe/Berlin]',
        'lastUpdatedBy': 'string[python]',
        'categoryId': 'int',
        'categoryDisplay': 'string[python]',
        'accountClass': 'string[python]',
        'taxId': 'datetime64[ns, Europe/Berlin]',
        'taxName': 'string[python]',
        'currencyId': 'string[python]',
        'currencyCode': 'string[python]',
        'number': 'str',
        'name': 'string[python]',
        'custom': 'string[python]',
        'notes': 'string[python]',
        'attachmentCount': 'Int64',
        'allocationCount': 'Int64',
        'costCenterIds': 'string[python]',
        'costCenterNumbers': 'string[python]',
        'openingAmount': 'Int64',
        'endAmount': 'Int64',
        'targetMin': 'string[python]',
        'targetMax': 'string[python]',
        'targetDisplay': 'string[python]',
        'defaultCurrencyOpeningAmount': 'Int64',
        'defaultCurrencyEndAmount': 'Int64',
        'isInactive': 'bool'
}
JOURNAL_ENTRIES = {
        'id': 'int',
        'created': 'datetime64[ns, Europe/Berlin]',
        'createdBy': 'string[python]',
        'lastUpdated': 'datetime64[ns, Europe/Berlin]',
        'lastUpdatedBy': 'string[python]',
        'debitId': 'int',
        'debitName': 'string[python]',
        'creditId': 'int',
        'creditName': 'string[python]',
        'associateId': 'Int64',
        'associateName': 'string[python]',
        'taxId': 'Int64',
        'taxName': 'string[python]',
        'orderId': 'Int64',
        'orderBookEntryId': 'Int64',
        'inventoryId': 'Int64',
        'importEntryId': 'Int64',
        'type': 'string[python]',
        'dateAdded': 'datetime64[ns, Europe/Berlin]',
        'title': 'string[python]',
        'custom': 'string[python]',
        'notes': 'string[python]',
        'reference': 'string[python]',
        'amount': 'float64',
        'currencyId': 'Int64',
        'currencyRate': 'float64',
        'currencyCode': 'string[python]',
        'accountId': 'Int64',
        'accountCurrencyId': 'Int64',
        'accountClass': 'string[python]',
        'balance': 'Int64',
        'nameSingular': 'string[python]',
        'orderType': 'string[python]',
        'itemsCount': 'int',
        'recurrence': 'string[python]',
        'startDate': 'string[python]',
        'endDate': 'string[python]',
        'daysBefore': 'Int64',
        'notifyType': 'string[python]',
        'notifyPersonId': 'Int64',
        'notifyUserId': 'Int64',
        'notifyEmail': 'string[python]',
        'attachmentCount': 'int',
        'allocationCount': 'int',
        'costCenterIds': 'Int64',
        'imported': 'string[python]',
        'importedBy': 'string[python]',
        'costCenterNumbers': 'Int64',
        'isRecurring': 'bool'
}