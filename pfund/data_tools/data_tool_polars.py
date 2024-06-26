from __future__ import annotations
from collections import defaultdict

from typing import TYPE_CHECKING, Generator
if TYPE_CHECKING:
    from pfund.datas.data_base import BaseData
    from pfund.models.model_base import BaseModel
    
import polars as pl

from pfund.strategies.strategy_base import BaseStrategy
from pfund.data_tools.data_tool_base import BaseDataTool
from pfund.utils.envs import backtest


class PolarsDataTool(BaseDataTool):
    def get_df(self, copy=True):
        return self.df.clone() if copy else self.df
    
    def prepare_df(self):
        assert self._raw_dfs, "No data is found, make sure add_data(...) is called correctly"
        self.df = pl.concat(self._raw_dfs.values())
        self.df = self.df.sort(by=self.index, descending=False)
        # arrange columns
        self.df = self.df.select(self.index + [col for col in self.df.columns if col not in self.index])
        self._raw_dfs.clear()
    
    @staticmethod
    @backtest
    def iterate_df_by_chunks(lf: pl.LazyFrame, num_chunks=1) -> Generator[pl.DataFrame, None, None]:
        total_rows = lf.count().collect()['ts'][0]
        chunk_size = total_rows // num_chunks
        for i in range(0, total_rows, chunk_size):
            df_chunk = lf.slice(i, chunk_size).collect()
            yield df_chunk
    
    @backtest
    def preprocess_event_driven_df(self, df: pl.DataFrame) -> pl.DataFrame:
        def _check_resolution(res):
            from pfund.datas.resolution import Resolution
            resolution = Resolution(res)
            return {
                'is_quote': resolution.is_quote(),
                'is_tick': resolution.is_tick()
            }
    
        df = df.with_columns(
            # converts 'ts' from datetime to unix timestamp
            pl.col("ts").cast(pl.Int64) // 10**6 / 10**3,
            
            # add 'broker', 'is_quote', 'is_tick' columns
            pl.col('product').str.split("-").list.get(0).alias("broker"),
            pl.col('resolution').map_elements(
                _check_resolution,
                return_dtype=pl.Struct([
                    pl.Field('is_quote', pl.Boolean), 
                    pl.Field('is_tick', pl.Boolean)
                ])
            ).alias('Resolution')
        ).unnest('Resolution')
        
        # arrange columns
        left_cols = self.index + ['broker', 'is_quote', 'is_tick']
        df = df.select(left_cols + [col for col in df.columns if col not in left_cols])
        return df
    
    # TODO
    @backtest
    def preprocess_vectorized_df(self, df: pl.DataFrame, strategy: BaseStrategy) -> pl.DataFrame:
        pass
    
    # TODO
    @staticmethod
    @backtest
    def postprocess_vectorized_df(df_chunks: list[pl.DataFrame]) -> pl.LazyFrame:
        df = pl.concat(df_chunks)
        return df.lazy()
    
    # TODO: for train engine
    def prepare_datasets(self, datas):
        pass
    
    def clear_df(self):
        self.df.clear()
    
    # TODO:
    def append_to_df(self, data: BaseData, predictions: dict, **kwargs):
        pass

    
    '''
    ************************************************
    Helper Functions
    ************************************************
    '''
    @staticmethod
    def output_df_to_parquet(df: pl.DataFrame | pl.LazyFrame, file_path: str, compression: str='zstd'):
        df.write_parquet(file_path, compression=compression)
    
    # TODO
    @staticmethod
    def filter_df(df: pl.DataFrame | pl.LazyFrame, **kwargs) -> pl.DataFrame | pl.LazyFrame:
        pass
    
    # TODO
    @staticmethod
    def unstack_df(df: pl.DataFrame | pl.LazyFrame, **kwargs) -> pl.DataFrame | pl.LazyFrame:
        pass