import os

import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from pymilvus import (
    connections,
    FieldSchema, CollectionSchema, DataType,
    Collection,
    utility
)

from pymilvus import MilvusClient
from pymilvus import model as milvus_model

from utils import embedding_model

class LocalMilvusDB:
    """
    基于 Milvus Lite 的本地向量数据库封装
    
    功能：
    - 在本地运行 Milvus 实例
    - 创建集合（collection）
    - 插入向量数据
    - 执行向量搜索
    - 数据持久化到本地文件
    
    使用示例：
    >>> db = LocalMilvusDB(persist_path="./milvus_data")
    >>> db.create_collection("my_collection", 128)
    >>> vectors = np.random.rand(100, 128).astype(np.float32).tolist()
    >>> db.insert("my_collection", vectors)
    >>> results = db.search("my_collection", np.random.rand(128).tolist(), top_k=5)
    """
    
    def __init__(self, persist_path: str = "./milvus_data"):
        """
        初始化本地 Milvus 数据库
        
        参数:
        persist_path: 数据持久化存储路径
        """
        self.persist_path = persist_path
        print("即将初始化")
        # 连接到本地 Milvus 实例
        self._connect()
    
    def _connect(self):
        """连接到本地 Milvus 实例"""
        try:
            self.milvus_client = MilvusClient(uri=self.persist_path)
            print(f"成功创建本地 Milvus 实例，数据存储在: {self.persist_path}")
        except Exception as e:
            print(f"创建 Milvus 失败: {e}")
            raise
    
    def create_collection(
        self, 
        collection_name: str, 
        dimension: int, 
        metric_type: str = "IP"
    ) -> bool:
        """
        创建新的集合
        
        参数:
        collection_name: 集合名称
        dimension: 向量维度
        metric_type: 距离度量类型（"L2" 或 "IP"）
        
        返回:
        是否创建成功
        """
        # 检查集合是否已存在
        if self.milvus_client.has_collection(collection_name):
            print(f"集合 '{collection_name}' 已存在，即将删除并重新创建")
            self.milvus_client.drop_collection(collection_name)
        
        
        try:
            # 创建集合
            self.milvus_client.create_collection(
                collection_name=collection_name,
                dimension=dimension,
                metric_type=metric_type,
                consistency_level="Strong",  # 支持的值为 (`"Strong"`, `"Session"`, `"Bounded"`, `"Eventually"`)。更多详情请参见 https://milvus.io/docs/consistency.md#Consistency-Level。
            )
            
            print(f"成功创建集合 '{collection_name}'，维度: {dimension}")
            return True
        except Exception as e:
            print(f"创建集合失败: {e}")
            return False
    
    def insert(
        self, 
        collection_name: str, 
        data: list
    ) -> bool:
        """
        向集合中插入向量数据
        
        参数:
        collection_name: 集合名称
        vectors: 向量列表（每个向量是浮点数列表）
        metadata: 元数据字典列表（可选）
        
        返回:
        是否插入成功
        """
        if not self.milvus_client.has_collection(collection_name):
            print(f"集合 '{collection_name}' 不存在")
            return False
        
        try:
            self.milvus_client.insert(collection_name=collection_name, data=data)
            print(f"成功插入 {data} 到 '{collection_name}'")
            return True
        except Exception as e:
            print(f"插入数据失败: {e}")
            return False
    
    def search(
        self, 
        collection_name: str, 
        question: str,
        metric_type: str = "IP",
        top_k: int = 3
    ) -> List[Dict]:
        """
        执行向量搜索
        
        参数:
        collection_name: 集合名称
        query_vector: 查询向量（浮点数列表）
        top_k: 返回的最相似结果数量
        output_fields: 返回的元数据字段（可选）
        
        返回:
        结果字典列表，每个字典包含:
        - 'id': 向量ID
        - 'distance': 距离
        - 'metadata': 元数据字典
        """
        if not self.milvus_client.has_collection(collection_name):
            print(f"集合 '{collection_name}' 不存在")
            return []
        
        try:
           
            search_res = self.milvus_client.search(
                            collection_name=collection_name,
                            data=embedding_model.encode_queries(
                                [question]
                            ),  # 将问题转换为嵌入向量
                            limit=top_k,  # 返回前3个结果
                            search_params={"metric_type": metric_type, "params": {}},  # 内积距离
                            output_fields=["text"],  # 返回 text 字段
                            )
            
            retrieved_lines_with_distances = [
                (res["entity"]["text"], res["distance"]) for res in search_res[0]
            ]
            print(f"在 '{collection_name}' 中找到 {len(retrieved_lines_with_distances)} 个结果")
            return retrieved_lines_with_distances
        except Exception as e:
            print(f"搜索失败: {e}")
            return []
    
    
    def list_collections(self) -> List[str]:
        """列出所有集合"""
        return self.milvus_client.list_collections()
    
    def collection_exists(self, collection_name: str) -> bool:
        """检查集合是否存在"""
        return self.milvus_client.has_collection(collection_name)

db = LocalMilvusDB(persist_path="./milvus_data.db")   