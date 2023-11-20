'''
This script send qt widget use data to the Fusion Trust dashboard

To use Call the main function with Command Line Arguments
Example: python send_qt_data_to_dashboard.py 20000

'''
from datetime import datetime
from os import environ
import requests
import sys


FCSDK_ITEM_ID = '73da45ae-5777-47dc-bdab-1cc3d62935a0'


class Fcs():
    '''Fcs utils '''

    def __init__(self) -> None:
        self.fc_collection_id = '5133c1d7-5bef-4337-9db0-b286f32ef7de'
        self.fc_library_id = '47c468d9-faa2-4d27-9a54-fcccf93dbb4c'
        self.host = 'https://developer.api.autodesk.com/'
        self.fcs_url = f'{self.host}/content/v2/collections'
        self.libraries = f'{self.fcs_url}/{self.fc_collection_id}/libraries'
        self.header = {'Accept': 'application/json',
                       'Content-Type': 'application/json', }

    def get_token(self):
        '''Get forge token'''

        req = requests.post(
            self.host + '/authentication/v1/authenticate',
            headers={
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            data=dict(
                client_id = environ.get("CLIENT_ID"),
                client_secret = environ.get("CLIENT_SECRET"),
                grant_type='client_credentials',
                scope='data:read data:write bucket:create data:search'
            ), timeout=60)
        token = req.json()
        self.header['Authorization'] = f"Bearer {token['access_token']}"
        return self.header

    def update_fcs_item(self, data, item_id):
        '''update and fcs record'''
        self.get_token()
        url = f'/{self.fc_library_id}/content-items/{item_id}'

        req = requests.put(self.libraries + url, headers=self.header,
                           json=data, timeout=60)

        if req.status_code in [202, 200]:
            print('Successfully sent qwidget data to the dashboard')
            print(req.content)
        else:
            print(
                f'Sending to dashboard failed with status code {req.status_code}')

        return req.json()

    def get_fcs_item(self, item_id, external_id=False):
        '''update and fcs record'''
        ext = 'true' if external_id else 'false'
        self.get_token()
        url = f'/{self.fc_library_id}/content-items/{item_id}?externalId={ext}'
        req = requests.get(self.libraries + url,
                           headers=self.header, timeout=60)

        return req.json()


def send_to_dashboard(qwidget_ocurrences, qwidget_occurrence_files_count):
    '''send qwidgetOcurrences data to Forge content'''
    fcs = Fcs()
    fcs_data = fcs.get_fcs_item(FCSDK_ITEM_ID)
    today = datetime.today().strftime('%Y-%m-%d')
    fcs_data['components']['staticChecker']['qwidgetOcurrences'][today] = qwidget_ocurrences

    # When we send a new proterty of data to FCS, first we need to create the property in FCS data components.
    # example: Here we are creating a new property call "qwidgetOcurrencesFilesCount" under "staticChecker".
    #   fcs_data['components']['staticChecker']['qwidgetOcurrencesFilesCount'] = dict()
    #
    # Once the property is created in the FCS data components we don't need to create it again. 

    fcs_data['components']['staticChecker']['qwidgetOcurrencesFilesCount'][today] = qwidget_occurrence_files_count

    fcs.update_fcs_item(fcs_data, FCSDK_ITEM_ID)
    new_fcs_data = fcs.get_fcs_item(FCSDK_ITEM_ID)
    qt_widget = new_fcs_data['components']['staticChecker']['qwidgetOcurrences']
    qwidget_occurrence_files_count_data = new_fcs_data['components']['staticChecker']['qwidgetOcurrencesFilesCount']

    if qt_widget[today] == qwidget_ocurrences:
        print('======================================================')
        print('QT widget ocurrences Data was saved to the dashbooard')
        print('======================================================')

    if qwidget_occurrence_files_count_data[today] == qwidget_occurrence_files_count:
        print('======================================================')
        print('QWidget ocurrence files count data was saved to the dashbooard')
        print('======================================================')
