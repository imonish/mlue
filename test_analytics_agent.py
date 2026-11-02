
from pprint import pprint

from backend.agents.analytics_agent import AnalyticsAgent


def main():

    print("=" * 60)
    print("MLUE - ANALYTICS AGENT TEST")
    print("=" * 60)

    agent = AnalyticsAgent()

    try:

        print("\n1. DATASET PROFILE")
        pprint(agent.run("profile"))

        print("\n2. REVENUE ANALYSIS")
        pprint(agent.run("revenue"))

        print("\n3. CORRELATION ANALYSIS")
        pprint(agent.run("correlation"))

    finally:
        agent.close()


if __name__ == "__main__":
    main()
