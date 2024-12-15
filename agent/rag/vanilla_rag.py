from agrag.agrag import AutoGluonRAG


def ag_rag():
    agrag = AutoGluonRAG(
        config_file="/Users/siyengar/Desktop/dev/Chemical/autogluon-rag/src/agrag/configs/presets/yash_config.yaml",
        data_dir="/Users/siyengar/Desktop/dev/Chemical/agent/knowledge_base",  # Directory containing files to use for RAG
    )

    agrag.initialize_rag_pipeline()
    while True:
        query_text = input(
            "Please enter a query for your RAG pipeline, based on the documents you provided (type 'q' to quit): "
        )
        if query_text == "q":
            break

        agrag.generate_response(query_text)


if __name__ == "__main__":
    ag_rag()
