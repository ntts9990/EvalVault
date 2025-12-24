"""Knowledge Graph Generator Demonstration.

This script demonstrates how to use the KnowledgeGraphGenerator to create
test questions from insurance documents.
"""

from evalvault.domain.services.kg_generator import KnowledgeGraphGenerator


def main():
    """Run knowledge graph generator demonstration."""
    # Sample insurance documents (Korean)
    documents = [
        "삼성생명의 종신보험은 사망보험금 1억원을 보장합니다. 월 보험료는 30만원입니다.",
        "한화생명의 암보험은 암 진단 시 5천만원을 지급합니다. 보험 기간은 10년입니다.",
        "교보생명의 연금보험은 월 50만원의 연금을 20년간 지급합니다.",
        "종신보험의 보험료는 월 30만원이며, 납입 기간은 20년입니다.",
        "암보험은 암진단비와 수술비, 입원비를 보장합니다.",
    ]

    # Create knowledge graph generator
    generator = KnowledgeGraphGenerator()

    # Build knowledge graph from documents
    print("=== Building Knowledge Graph ===")
    generator.build_graph(documents)

    # Get statistics
    stats = generator.get_statistics()
    print(f"\nGraph Statistics:")
    print(f"  Total entities: {stats['num_entities']}")
    print(f"  Total relations: {stats['num_relations']}")
    print(f"  Entity types: {stats['entity_types']}")

    # Generate simple questions
    print("\n=== Simple Questions ===")
    simple_questions = generator.generate_questions(num_questions=5)
    for i, tc in enumerate(simple_questions, 1):
        print(f"\n{i}. Question: {tc.question}")
        print(f"   Entity: {tc.metadata.get('entity')}")
        print(f"   Type: {tc.metadata.get('entity_type')}")
        print(f"   Context: {tc.contexts[0][:50]}...")

    # Generate multi-hop questions
    print("\n=== Multi-hop Questions (2 hops) ===")
    multi_hop = generator.generate_multi_hop_questions(hops=2)
    for i, tc in enumerate(multi_hop, 1):
        print(f"\n{i}. Question: {tc.question}")
        print(f"   Path: {tc.metadata.get('path')}")

    # Generate comparison questions
    print("\n=== Comparison Questions ===")
    comparison = generator.generate_comparison_questions(num_questions=2)
    for i, tc in enumerate(comparison, 1):
        print(f"\n{i}. Question: {tc.question}")
        print(f"   Entities: {tc.metadata.get('entities')}")

    # Generate complete dataset
    print("\n=== Complete Dataset ===")
    dataset = generator.generate_dataset(
        num_questions=10, name="insurance-kg-testset", version="1.0.0"
    )
    print(f"\nDataset: {dataset.name} v{dataset.version}")
    print(f"Total test cases: {len(dataset.test_cases)}")
    print(f"Metadata: {dataset.metadata}")

    # Generate questions by entity type
    print("\n=== Questions by Entity Type ===")
    org_questions = generator.generate_questions_by_type("organization", num_questions=2)
    print(f"\nOrganization questions: {len(org_questions)}")
    for tc in org_questions:
        print(f"  - {tc.question}")

    product_questions = generator.generate_questions_by_type("product", num_questions=2)
    print(f"\nProduct questions: {len(product_questions)}")
    for tc in product_questions:
        print(f"  - {tc.question}")


if __name__ == "__main__":
    main()
