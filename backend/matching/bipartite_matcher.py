class BipartiteMatcher:

    def match(self, score_matrix):
        """
        Find a maximum-weight matching.

        score_matrix[i][j] =
            score of assigning rider i to driver j

        Returns:
            list of (rider_index, driver_index, score)
        """

        if not score_matrix:
            return []

        original_rows = len(score_matrix)
        original_cols = len(score_matrix[0])

        # Hungarian implementation expects
        # rows <= columns.
        transposed = False

        if original_rows > original_cols:
            score_matrix = self._transpose(score_matrix)
            transposed = True

        n = len(score_matrix)
        m = len(score_matrix[0])

        max_score = max(
            max(row) for row in score_matrix
        )

        # Convert maximization into minimization.
        cost = [
            [
                max_score - score_matrix[i][j]
                for j in range(m)
            ]
            for i in range(n)
        ]

        # Hungarian algorithm
        u = [0] * (n + 1)
        v = [0] * (m + 1)

        p = [0] * (m + 1)
        way = [0] * (m + 1)

        for i in range(1, n + 1):

            p[0] = i
            j0 = 0

            minv = [float("inf")] * (m + 1)
            used = [False] * (m + 1)

            while True:

                used[j0] = True

                i0 = p[j0]
                delta = float("inf")
                j1 = 0

                for j in range(1, m + 1):

                    if used[j]:
                        continue

                    cur = (
                        cost[i0 - 1][j - 1]
                        - u[i0]
                        - v[j]
                    )

                    if cur < minv[j]:
                        minv[j] = cur
                        way[j] = j0

                    if minv[j] < delta:
                        delta = minv[j]
                        j1 = j

                for j in range(m + 1):

                    if used[j]:
                        u[p[j]] += delta
                        v[j] -= delta
                    else:
                        minv[j] -= delta

                j0 = j1

                if p[j0] == 0:
                    break

            while True:

                j1 = way[j0]
                p[j0] = p[j1]
                j0 = j1

                if j0 == 0:
                    break

        matches = []

        for j in range(1, m + 1):

            if p[j] == 0:
                continue

            row = p[j] - 1
            col = j - 1

            if transposed:
                rider_index = col
                driver_index = row
            else:
                rider_index = row
                driver_index = col

            score = score_matrix[
                row
            ][
                col
            ]

            matches.append(
                (
                    rider_index,
                    driver_index,
                    score
                )
            )

        return matches

    @staticmethod
    def _transpose(matrix):
        return [
            list(row)
            for row in zip(*matrix)
        ]