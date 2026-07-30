import os
import glob

class MatrixParser:
    def __init__(self, matrix_dir="references/knowledge-matrix"):
        self.matrix_dir = matrix_dir
        self.files = glob.glob(os.path.join(self.matrix_dir, "*.md"))

    def search_matrix(self, keyword: str) -> dict:
        """
        Searches the knowledge matrix markdown files for the given keyword.
        Returns a dictionary mapping filenames to lists of matching lines.
        """
        results = {}
        for filepath in self.files:
            filename = os.path.basename(filepath)
            matches = []
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    for i, line in enumerate(f):
                        if keyword.lower() in line.lower():
                            matches.append({"line_num": i + 1, "content": line.strip()})
            except Exception as e:
                print(f"Error reading {filepath}: {e}")

            if matches:
                results[filename] = matches

        return results

if __name__ == "__main__":
    # Test
    parser = MatrixParser()
    print("Test search 'Bc-Ⅳ-3':")
    res = parser.search_matrix("Bc-Ⅳ-3")
    print(res)
