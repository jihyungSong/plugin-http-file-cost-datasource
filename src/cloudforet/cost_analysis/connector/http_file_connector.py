import logging
import copy
import pandas as pd
import numpy as np

from spaceone.core.transaction import Transaction
from spaceone.core.connector import BaseConnector
from typing import List

from cloudforet.cost_analysis.error import *

__all__ = ['HTTPFileConnector']

_LOGGER = logging.getLogger(__name__)

_REQUIRED_CSV_COLUMNS = [
    'cost',
    'currency',
    'year',
    'month',
    'day'
]

_PAGE_SIZE = 1000


class HTTPFileConnector(BaseConnector):

    def __init__(self, transaction: Transaction, config: dict = None):
        super().__init__(transaction, config)
        self.base_url = None
        self.header_columns = None

    def create_session(self, options: dict, secret_data: dict, schema: str = None) -> None:
        self._check_options(options)
        self.base_url = options['base_url']

        if 'header_columns' in options:
            self.header_columns = options['header_columns']

    def get_cost_data(self, base_url):
        _LOGGER.debug(f'[get_cost_data] base url: {base_url}')

        costs_data = self._get_csv(base_url)

        _LOGGER.debug(f'[get_cost_data] costs count: {len(costs_data)}')

        # Paginate
        page_count = int(len(costs_data) / _PAGE_SIZE) + 1

        for page_num in range(page_count):
            offset = _PAGE_SIZE * page_num
            yield costs_data[offset:offset + _PAGE_SIZE]

    @staticmethod
    def _check_options(options: dict) -> None:
        if 'base_url' not in options:
            raise ERROR_REQUIRED_PARAMETER(key='options.base_url')

    def _get_csv(self, base_url: str) -> List[dict]:
        try:
            df = pd.read_csv(base_url, header=0, sep=',')
            df = df.replace({np.nan: None})

            if self.header_columns:
                for key, value in self.header_columns.items():
                    df.rename(columns={key: value}, inplace=True)

            self._check_required_columns(df)

            costs_data = df.to_dict('records')
            return costs_data
        except Exception as e:
            _LOGGER.error(f'[_get_csv] download error: {e}', exc_info=True)
            raise e

    @staticmethod
    def _check_required_columns(data_frame):
        for column in _REQUIRED_CSV_COLUMNS:
            if column not in data_frame.columns:
                _LOGGER.error(f'[_check_columns] invalid required columns: {column}', exc_info=True)
                raise ERROR_INVALID_COLUMN(column=column)
