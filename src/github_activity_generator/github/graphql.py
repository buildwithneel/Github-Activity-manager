"""GitHub GraphQL queries for contributionCalendar retrieval."""

CONTRIBUTION_YEARS_QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionYears
    }
  }
}
"""

CONTRIBUTION_CALENDAR_QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      totalCommitContributions
      totalIssueContributions
      totalPullRequestContributions
      totalPullRequestReviewContributions
      restrictedContributionsCount
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
            weekday
            color
          }
        }
      }
    }
  }
}
"""
