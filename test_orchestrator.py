from pprint import pprint
from backend.orchestration.graph import MLUEOrchestrator


def main():
    orchestrator = MLUEOrchestrator()

    try:
        questions = [
            "What is total revenue?",
            "Show me a dataset profile",
            "Forecast sales for the next 5 days",
        ]

        for question in questions:
            print("\n" + "=" * 60)
            pprint(orchestrator.run(question))

    finally:
        orchestrator.close()


if __name__ == "__main__":
    main()