import json, os, pandas as pd, requests
from mimetypes import guess_type
from pathlib import Path

class CashCtrlAPIClient:
    """
    A lightweight wrapper to facilitate interactions with the CashCtrl REST API.

    See package README for an overview and for usage examples: https://github.com/macxred/cashctrl_api
    """
    def __init__(self,
                 organisation=os.getenv("CC_API_ORGANISATION"),
                 api_key=os.getenv("CC_API_KEY")):
        """
        Parameters:
            organisation (str): The sub-domain of the organization as configured in CashCtrl.
                                Defaults to the value of the `CC_API_ORGANISATION`
                                environment variable if not explicitly provided.
            api_key (str): The API key used for authenticating with the CashCtrl API.
                        Defaults to the value of the `CC_API_KEY` environment variable
                        if not explicitly provided.
        """
        self._api_key = api_key
        self._base_url = f"https://{organisation}.cashctrl.com/api/v1"

    def _request(self, method, endpoint, data=None, params={}):

        # The CashCtrl API does not accept nested json data structures,
        # we need to convert nested lists and dicts to string representation.
        # See https://forum.cashctrl.com/d/644-adresse-anlegen-ueber-api
        def flatten(d):
            if d is None:
                return None
            else:
                return {k: (json.dumps(v) if isinstance(v, (list, dict)) else v)
                        for k, v in d.items()}

        url = f"{self._base_url}/{endpoint}"
        response = requests.request(method, url, auth=(self._api_key, ''), data=flatten(data), params=flatten(params))
        if response.status_code != 200:
            raise requests.HTTPError(f"API request failed with status {response.status_code}: {response.text}")
        result = response.json()

        # Enforce 'success' (if field is present)
        if ('success' in result) and (not result['success']):
            msg = result.get('message', None)
            if msg is None:
                errors = result.get('errors', [])
                msg = " / ".join(error.get('message', '')
                                 for error in errors if 'message' in error)
            if msg == '':
                msg = '(no message)'
            raise requests.RequestException(f"API call failed with message: {msg}")

        return result

    def get(self, endpoint, data=None, params={}):
        return self._request("GET", endpoint, data=data, params=params)

    def post(self, endpoint, data=None, params={}):
        return self._request("POST", endpoint, data=data, params=params)

    def put(self, endpoint, data=None, params={}):
        return self._request("PUT", endpoint, data=data, params=params)

    def delete(self, endpoint, data=None, params={}):
        return self._request("DELETE", endpoint=None, data=data, params=params)


    def file_upload(self, local_path, remote_name=None, remote_category=None, mime_type=None):
        """
        Uploads a file to the server and marks it for persistent storage.

        Parameters:
            local_path (str|Path): Path to a local file to upload.
            remote_name (str): The filename on the remote server; defaults to the name of the local file.
            remote_category (id, optional): The category under which the file should be stored.
            mime_type (str, optional): The MIME type of the file. If None, the MIME type will be guessed from the file extension.

        Returns:
            The Id of the newly created object.
        """
        # init and checks
        mypath = Path(local_path).expanduser().resolve()
        if not mypath.is_file():
            raise FileNotFoundError(f"File not found: '{mypath}'.")
        if remote_name is None: remote_name = mypath.name
        if mime_type is None: mime_type = guess_type(mypath)[0]

        # step (1/3: prepare)
        if remote_category is None:
            myfilelist = [{"mimeType": mime_type, "name": remote_name}]
        else:
            myfilelist = [{"mimeType": mime_type, "name": remote_name, 'categoryId': remote_category}]
        response = self.post("file/prepare.json", params={'files': myfilelist})
        myid = response['data'][0]['fileId']
        write_url = response['data'][0]['writeUrl']

        # step (2/3): upload
        with open(mypath, 'rb') as f:
            response = requests.put(write_url, files={str(mypath): f})
        if response.status_code != 200:
            raise requests.RequestException(f"File upload failed (status {response.status_code}): {response.reason}.")

        # step (3/3): persist
        self.post("file/persist.json", params={'ids': myid})
        return myid


    def list_categories(self, object: str, system: bool=False) -> pd.DataFrame:
        """
        Retrieves a category tree and converts the nested categories into a flat pd.DataFrame.
        Each node's hierarchical position is described as a 'path' in Unix-like filepath format.
        The function works for all CashCtrl object types with associated category trees, such as 'account', 'file', etc.

        For the 'file' object a 'rootpath' field will be added where the string 'Alle Dateien' will be
        replaced by 'ROOT'. This protects from cumbersome language/path details and is much simpler to
        look at and work with. The `mirror_files` method depends on this.

        Parameters:
            object (str): Specifies the CashCtrl object type with an associated category tree.
                        Examples include 'account', 'file', etc.
            system (bool, optional): Determines whether system-generated nodes should be included in the result.
                                    If True, system nodes are included. If False (default), system nodes are excluded.
            level (int): indicates depth of nesting, root category (and trash) has '0' value.
            rootpath (str): path where 'Alle Dateien' has been replaced by 'ROOT' (only for 'file' objects)

        Returns:
            pd.DataFrame: A DataFrame containing the flattened category tree. Each row represents a category,
                        with a 'path' column indicating the category's hierarchical position in Unix-like filepath format.
                        The path's root name depends on the object type and the current UI language setting.
                        Additional columns correspond to properties of each category node.
        """
        def flatten_data(nodes, parent_path=''):
            if not isinstance(nodes, list):
                raise ValueError(f"Expecting `nodes' to be a list, not {type(nodes)}.")
            rows = []
            for node in nodes:
                path = f"{parent_path}/{node['text']}"
                if ('data' in node) and (not node['data'] is None):
                    data = node.pop('data')
                    rows.extend(flatten_data(data, path))
                rows.append({'path': path} | node)
            return rows

        data = self.get(f"{object}/category/tree.json")['data']
        df = pd.DataFrame(flatten_data(data.copy()))
        if object == 'file':
            df['rootpath'] = df['path'].str.replace('/All files', '/ROOT', regex=False)
        df['level'] = df['path'].apply(lambda x: x.count('/') - 1)
        if not system:
            df = df.loc[~df['isSystem'], :]
        return df.sort_values('path')

    def _remote_filepath_list(self):
        """
        Get a table with all files incl. path (i.e. category) from the server.
        Columns: id, catid, filename, path, rootpath, mimetype, size, ctime, mtime
        """
        xcat = self.list_categories('file')
        xcat.rename(columns={'id': 'catId'}, inplace=True)

        xfile = pd.DataFrame(self.get("file/list.json")['data'])
        xfile = xfile[['id', 'categoryId', 'name', 'mimeType', 'size', 'created', 'lastUpdated']]
        xfile = xfile.sort_values(['categoryId', 'name'])

        merged_df = pd.merge(xfile, xcat[['catId', 'text', 'path']], left_on='categoryId', right_on='catId', how='left')
        merged_df['path'] = merged_df['path'] + '/' + merged_df['name']
        merged_df.drop(['text', 'catId'], axis=1, inplace=True)
        merged_df.rename(columns={'name': 'filename'}, inplace=True)
        merged_df.rename(columns={'categoryId': 'catid'}, inplace=True)
        merged_df.rename(columns={'mimeType': 'mimetype'}, inplace=True)
        merged_df.rename(columns={'created': 'ctime'}, inplace=True)
        merged_df.rename(columns={'lastUpdated': 'mtime'}, inplace=True)
        merged_df = merged_df[['id', 'catid', 'filename', 'path', 'mimetype', 'size', 'ctime', 'mtime' ]]

        # check path and replace 'All files' with 'ROOT'
        if not merged_df['path'].str.startswith('/All files').all():
            raise Exception("path does not start with '/All files'")
        merged_df['rootpath'] = merged_df['path'].str.replace('/All files', '/ROOT', regex=False)
        merged_df = merged_df[['id', 'catid', 'filename', 'path', 'rootpath', 'mimetype', 'size', 'ctime', 'mtime' ]]
        return merged_df

    def _local_filepath_list(self, root):
        """
        Get a table with all files incl. path from the root folder, skip hidden files.
        Columns: filename, path, rootpath, mimetype, size, ctime, mtime
        """

        def _stat_to_json(file):
            """from : https://stackoverflow.com/a/58684090/9770860"""
            stat = file.stat()
            attributes = {k[3:]: getattr(stat, k) for k in dir(stat) if k.startswith('st_')}
            return {'file': str(file)} | attributes

        rootpath = Path(root).expanduser()
        files = [file for file in rootpath.rglob("*") if (file.is_file()) and (file.name[0] != '.')]
        df = pd.DataFrame([_stat_to_json(file) for file in files])
        df['ctime'] = pd.to_datetime(df['ctime_ns'], unit='ns').dt.tz_localize('UTC')
        df['mtime'] = pd.to_datetime(df['mtime_ns'], unit='ns').dt.tz_localize('UTC')
        df.rename(columns={'file': 'path'}, inplace=True)

        if not df['path'].str.startswith(str(rootpath)).all():
            raise Exception(f"path does not start with '{rootpath}'")
        df['filename'] = df['path'].apply(lambda x: Path(x).name)
        df['rootpath'] = df['path'].str.replace(str(rootpath), '/ROOT', regex=False)
        df['mimetype'] = df['path'].apply(lambda x: guess_type(x)[0])
        df = df[['filename', 'path', 'rootpath', 'mimetype', 'size', 'ctime', 'mtime']]
        return df

    def _mirror_file_categories(self, local_files, remote_categories):
        local_folders = local_files['rootpath'].str.replace('/[^/]*$', '', regex=True).unique()
        local_folders = pd.DataFrame({'rootpath': local_folders}) # need a DataFrame for 'isin' set comparison

        ## step 1: erase orphaned nodes (path does not appear in any file path)
        ##         (IMPORTANT: trash must be empty as those files prevent category deletion)

        is_orphaned = [not any(local_files['rootpath'].str.startswith(node)) for node in remote_categories['rootpath']]
        orphaned = remote_categories.loc[is_orphaned,:].sort_values(by=['level', 'rootpath'], ascending = [False, False])
        delete_ids = ','.join(orphaned['id'].astype(str))
        if delete_ids != '': self.post("file/category/delete.json", params={'ids': delete_ids})

        ## step 2: add required categories

        # use the non-orphaned categories (orphaned ones have just been deleted above...)
        non_orphaned = [not x for x in is_orphaned]
        remote_categories = remote_categories.loc[non_orphaned,:]
        remote_categories_map = {k: v for k, v in zip(remote_categories['rootpath'], remote_categories['id'])}

        # which categories are missing?
        missing_category_idx = ~local_folders['rootpath'].isin(remote_categories['rootpath'])
        missing_categories = local_folders[missing_category_idx]

        # create missing categories (work from root to leaf)
        for category in missing_categories['rootpath']:
            category = category.lstrip('/')
            nodes = category.split('/')
            if nodes[0] != 'ROOT': raise Exception("'ROOT' node missing")
            # handle the 'nodes' of a single rootpath (from root to leaf)
            for i in range(1, len(nodes)):
                node_path = '/' + '/'.join(nodes[:(i+1)])
                if node_path == '/ROOT': continue
                parent_path = '/' + '/'.join(nodes[:i])
                # check remote_categories_map, node could have been added by another rootpath
                if not node_path in remote_categories_map:
                    if parent_path == '/ROOT':
                        parentid = 0
                    else:
                        parentid = remote_categories_map[parent_path]
                    # create category for real and add to the map
                    response = self.post("file/category/create.json", params={'name': nodes[i], 'parentId': parentid})
                    new_nodeid = response['insertId']
                    remote_categories_map[node_path] = new_nodeid

    def mirror_files(self, root):

        ## 1. Preparation (get remote/local files in uniform structure)

        remote_files = _remote_filepath_list(self)
        # rf = remote_files; print(rf); print(""); print(rf.iloc[0]); print(""); print(rf.iloc[0]['path'])
        local_files = _local_filepath_list(self, root)
        # lf = local_files; print(lf); print(""); print(lf.iloc[0]); print(""); print(lf.iloc[0]['path'])

        ## 2. File Deletion

        to_delete = ~remote_files['rootpath'].isin(local_files['rootpath'])
        if sum(to_delete) > 0:
            delidx = remote_files[to_delete]['id']
            # delete remote files, possibly orphaned folders/categories remain
            myids = ','.join(delidx.astype(str))
            self.post("file/delete.json", params={'ids': myids, 'force': True})
            remote_files = remote_files.loc[~to_delete,:]

        ## 3. Folder/Category Sync

        # Trash/Papierkorb *MUST* be empty. Trashed files might still belong
        # to a category and would prevent the deletion of an 'empty' category
        self.post("file/empty_archive.json")

        remote_categories = self.list_categories('file')
        _mirror_file_categories(self, local_files, remote_categories)

        ## 4.  Upload new or modified files

        # fetch categories again and compare local/remote file
        remote_categories = self.list_categories('file')
        remote_file_exists = local_files['rootpath'].isin(remote_files['rootpath'])
        remote_file_missing = [not x for x in remote_file_exists]

        # upload missing files
        uploads = local_files.loc[remote_file_missing]
        for row in uploads.to_dict('records'):
            papath = Path(row['rootpath']).parent
            catid = remote_categories.loc[remote_categories['rootpath'] == str(papath)]['id'].item()
            response = self.file_upload(row['path'], row['filename'], remote_category=catid)

        # TODO: handle modified files (mtime of local file after mtime of remote file)
        # FIXME:
        # - need 'POST /api/v1/file/update.json' (https://app.cashctrl.com/static/help/en/api/index.html#/file/update.json)
        # - this function is not (yet) implemented

    def _file_update(self, remote_file_id, remote_category_id, local_path, mime_type):
            """
            Updates an existing file on the server with a modified local one.
            This is a helper function where the caller must ensure that the given
            values are correct. There are no checks if e.g. file or category exists.

            Parameters:
                remote_file_id (int): The Id of the file to be replaced.
                remote_category_id (int): The Id of the category, None if on root level
                local_path (str|Path): Path to a local file to upload.
                mime_type (str): The MIME type of the file.
            """
            mypath = Path(local_path).expanduser().resolve()
            remote_name = mypath.name

            # step (1/2: prepare)
            if remote_category_id is None:
                myfiles = [{"mimeType": mime_type, "name": remote_name}]
            else:
                myfiles = [{"mimeType": mime_type, "name": remote_name, 'categoryId': remote_category_id}]
            response = self.post("file/prepare.json", params={'files': myfiles})
            myid = response['data'][0]['fileId']
            write_url = response['data'][0]['writeUrl']

            # step (2/3): upload
            with open(mypath, 'rb') as f:
                response = requests.put(write_url, files={str(mypath): f})
            if response.status_code != 200:
                raise requests.RequestException(f"File upload failed (status {response.status_code}): {response.reason}.")

            # step (3/3): replacement
            if remote_category_id is None:
                myparam = {"id": remote_file_id, "name": remote_name, "replaceWith": myid}
            else:
                myparam = {"id": remote_file_id, "name": remote_name, "categoryId": remote_category_id, "replaceWith": myid}

            response = self.post("file/update.json", params=myparam)
            return response