import json
import re
from typing import List, Dict, Any
from datetime import datetime

class ProductChunker:
    """
    产品数据chunking工具 - 从JSON文件读取数据并按产品进行chunking，可以保留好较完整的语义
    """
    
    def __init__(self, input_file: str, output_file: str = None):
        """
        初始化chunker
        
        Args:
            input_file: 输入JSON文件路径
            output_file: 输出文件路径（可选，默认为input_file_chunks.json）
        """
        self.input_file = input_file
        self.output_file = output_file or input_file.replace('.json', '_chunks.json')
        self.products_data = None
    
    def load_products_from_json(self) -> List[Dict[str, Any]]:
        """
        从JSON文件加载产品数据
        
        Returns:
            产品数据列表
        """
        try:
            with open(self.input_file, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            # 支持两种JSON格式：直接数组或包含"products"键的对象
            if isinstance(data, list):
                products_list = data
            elif "products" in data:
                products_list = data["products"]
            else:
                raise ValueError("JSON文件格式不支持：必须是产品列表或包含'products'键的对象")
            
            print(f"✅ 成功从 {self.input_file} 加载了 {len(products_list)} 个产品的数据")
            return products_list
            
        except FileNotFoundError:
            print(f"❌ 错误：文件 {self.input_file} 未找到")
            return []
        except json.JSONDecodeError as e:
            print(f"❌ 错误：JSON文件格式错误 - {e}")
            return []
        except Exception as e:
            print(f"❌ 读取文件时发生错误：{e}")
            return []
    
    def chunk_by_product(self) -> List[Dict[str, Any]]:
        """
        按产品进行chunking，每个产品作为一个完整的语义单元
        
        Returns:
            chunk列表
        """
        if self.products_data is None:
            self.products_data = self.load_products_from_json()
        
        if not self.products_data:
            print("⚠️ 没有可用的产品数据，请检查文件路径和内容")
            return []
        
        chunks = []
        
        for i, product in enumerate(self.products_data):
            # 构建完整的chunk内容
            chunk_content = self._format_product_chunk(product)
            
            # 提取元数据
            metadata = self._generate_metadata(product, i)
            
            chunk = {
                "chunk_id": f"product_{i}",
                "product_name": product.get("product_name", "未知产品"),
                "content": chunk_content,
                "metadata": metadata,
                "embedding_ready": True,
                "timestamp": datetime.now().isoformat()
            }
            chunks.append(chunk)
        
        print(f"✅ 成功生成 {len(chunks)} 个产品chunk")
        return chunks
    
    def _format_product_chunk(self, product: Dict) -> str:
        """格式化产品chunk的文本内容"""
        product_name = product.get("product_name", "未知产品")
        web_query = product.get("web_query", "")
        product_info = product.get("product_info", "")
        
        return f"""产品名称：{product_name}

                网络评价与热门话题：
                {web_query}

                产品详细信息：
                {product_info}"""
    
    def _generate_metadata(self, product: Dict, index: int) -> Dict[str, Any]:
        """为每个chunk生成丰富的元数据"""
        product_name = product.get("product_name", "未知产品")
        web_query = product.get("web_query", "")
        
        return {
            "source": "product_database",
            "chunk_type": "full_product",
            "product_name": product_name,
            "web_query_topics": self._extract_topics(web_query),
            "product_categories": self._categorize_product(product_name, product.get("product_info", "")),
            "content_length": len(self._format_product_chunk(product)),
            "chunk_index": index
        }
    
    def _extract_topics(self, web_query: str) -> List[str]:
        """从web_query中提取话题标签"""
        topics = re.findall(r'#\w+', web_query)
        return topics if topics else ["general_product"]
    
    def _categorize_product(self, product_name: str, product_info: str) -> List[str]:
        """根据产品名称和信息进行分类"""
        categories = []
        combined_text = (product_name + " " + product_info).lower()
        
        # 基于关键词的分类逻辑
        category_keywords = {
            "beauty_skincare": ['精华', '护肤', '面膜', '乳液', '化妆品', '美容', '肤质', '保湿'],
            "electronics": ['手环', '智能', '电子', '科技', '电池', '蓝牙', '显示屏', '防水'],
            "food_beverage": ['咖啡', '食品', '饮料', '风味', '食用', '饮品', '口感', '配方'],
            "home_textile": ['毛巾', '纺织', '棉', '布料', '洗涤', '抗菌', '吸水'],
            "sports_fitness": ['健身', '运动', '筋膜', '肌肉', '锻炼', '放松', '按摩']
        }
        
        for category, keywords in category_keywords.items():
            if any(keyword in combined_text for keyword in keywords):
                categories.append(category)
        
        return categories if categories else ["general"]
    
    def save_chunks_to_file(self, chunks: List[Dict[str, Any]]) -> bool:
        """
        将chunks保存到JSON文件
        
        Args:
            chunks: chunk列表
            
        Returns:
            是否保存成功
        """
        try:
            output_data = {
                "metadata": {
                    "source_file": self.input_file,
                    "generated_at": datetime.now().isoformat(),
                    "total_chunks": len(chunks),
                    "chunking_strategy": "by_product"
                },
                "chunks": chunks
            }
            
            with open(self.output_file, 'w', encoding='utf-8') as file:
                json.dump(output_data, file, ensure_ascii=False, indent=2)
            
            print(f"✅ 成功将 {len(chunks)} 个chunk保存到 {self.output_file}")
            return True
            
        except Exception as e:
            print(f"❌ 保存文件时发生错误：{e}")
            return False
    
    def prepare_for_vector_database(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        为向量数据库准备标准格式
        
        Args:
            chunks: 原始chunk列表
            
        Returns:
            向量数据库优化格式
        """
        vector_db_data = []
        
        for chunk in chunks:
            vector_item = {
                "id": chunk["chunk_id"],
                "text": chunk["content"],
                "metadata": chunk["metadata"],
                "product_name": chunk["product_name"]
            }
            vector_db_data.append(vector_item)
        
        return vector_db_data
    
    def print_chunks_as_json(self,chunks: any):
        """
        以JSON格式打印分块数据（适合程序处理）
        """
        print("\n" + "=" * 60)
        print("JSON格式输出")
        print("=" * 60)
        
        # 创建简化的JSON结构
        simplified_chunks = []
        for chunk in chunks:
            simplified = {
                "chunk_id": chunk.get("chunk_id"),
                "product_name": chunk.get("product_name"),
                "content_preview": chunk.get("content", "")[:150] + "..." if len(chunk.get("content", "")) > 150 else chunk.get("content", ""),
                "categories": chunk.get("metadata", {}).get("product_categories", [])
            }
            simplified_chunks.append(simplified)
        
        print(json.dumps(simplified_chunks, ensure_ascii=False, indent=2))