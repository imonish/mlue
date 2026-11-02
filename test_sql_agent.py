
from backend.agents.sql_agent import SQLAgent


def main():

    print("=" * 60)
    print("MLUE - SQL BUSINESS ANALYTICS AGENT")
    print("=" * 60)

    agent = SQLAgent()

    questions = [
        "What are the top 5 products by total revenue?",
        "What is the total revenue of all products?",
        "Which product has the highest quantity sold?",
    ]

    try:

        for question in questions:

            result = agent.run(question)

            print("\n" + "=" * 60)
            print("FINAL RESULT")
            print("=" * 60)

            if result["success"]:

                print("\nQuestion:")
                print(result["question"])

                print("\nSQL:")
                print(result["sql"])

                print("\nResults:")

                for row in result["rows"]:
                    print(row)

                print("\nRows returned:")
                print(result["row_count"])

                print("\nAttempts:")
                print(result["attempts"])

            else:

                print("Agent failed:")
                print(result["error"])

    finally:
        agent.close()


if __name__ == "__main__":
    main()
