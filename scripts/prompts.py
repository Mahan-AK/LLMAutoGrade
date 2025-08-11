solution_extract_instruction = """
Please parse and process the pdf file relating to the mathematics field. The file represents a model solution for a course. It contains mathematical equations and proofs and plots. Please extract all of the information in the file to the best of your ability and save the mathematical text as latex inside $$ tags in an overall markdown format. Only format the text and don't add in any other information.
"""

solution_parse_instruction = """
The given markdown file is parsed from the text data from a pdf file relating to the mathematics field. The file represents a model solution for a course. The problem is that the parsed document lacks visual data and clues from the pdf which is extremely important for a math document. Please, referencing the markdown file, edit, correct and complete the parsed document using the visual data gained from the image files. Pay attention to extracting information from plots, diagrams, tables, and other visual elements with their details. Keep the original text as much as possible except for corrections and don't lose any information.
"""

solution_parse_format_desc = """
Your output must be strictly parsable by an automated script.
To help you with this, you will be provided with a Structural Hint that outlines exercises, parts, sub-parts, and the specific points for each smallest gradable unit.

Markdown Formatting Rules:

Main Exercise Header:
- Format: ## Exercise X.Y (Descriptive Exercise Title). (Total: Z points)
    - X.Y: Use the exercise number exactly as in the hint.
    - Descriptive Exercise Title: Use the title provided in the data. Do not invent or modify.
    - (Total: Z points): Z is the sum of all points for gradable units in this exercise, as specified in the hint.

Part Headers (Containers/Grouping):
- If the hint shows a Roman numeral like i), ii) followed by indented sub-parts (e.g., a), b)), then this Roman numeral represents a grouping.
- Format: (roman_numeral) Part Title
    - Use the part title provided in the data. Do not invent or modify.
    - Do NOT add [N points] to container/grouping headers.

Smallest Gradable Unit Headers (Actual Questions):
- These are the lines that directly correspond to an entry in the Structural Hint that specifies points (e.g., a) 2 points, ii) 3 points, or if Exercise X.Y: N points implies a single gradable unit).
- Format: (identifier) Question Prompt Text. [N points]
    - identifier: Use exactly as in the hint (e.g., a), b), i), ii), etc.).
    - Question Prompt Text: Use the question text provided in the data. Do not invent or modify.
    - [N points]: N must match the points specified for that unit in the Structural Hint.

Single-Question Exercises:
- If the hint provides points directly for an Exercise X.Y without sub-parts, treat this as an exercise with a single gradable unit.
- Format:
    ## Exercise X.Y (Descriptive Title). (Total: N points)

    (i) The question for Exercise X.Y. [N points]
    **Solution.**
    The solution for Exercise X.Y.i.

Solutions:
- Every solution must start on a new line immediately following its gradable unit header.
- Prefix every solution with: **Solution.**

Here is the hint:
{structural_hint}
"""

solution_parse_fix_mistakes_instruction = """
This is a model solution document for the assignment and should be semantically and syntactically correct. There could be some small mistakes that were already in the file or were introduced when parsing the document. While formatting the document please also fix any inconsistencies or mistakes in the document.
"""

submission_extract_and_parse_instruction = """
Please parse and process the pdf file relating to the mathematics field. The file represents a submission for an assignment for a course. It contains mathematical equations and proofs and plots. Please extract all of the information in the file to the best of your ability and save the mathematical text as latex inside $$ tags in an overall markdown format.
You have access to the textual data from the pdf file. The challenge is that the textual pdf data lacks visual data and clues from the pdf which is extremely important for a math document. For this please use the visual context from the images of the submission and include descriptions of visual elements like plots, diagrams, and handwritten work.
It is very important that you only format the text and don't add in any other information because it will be used for grading. The contents of the submission may or may not be correct but must be parsed as is.
"""

grading_instruction = """
You are a math expert. You are given a submission for an assignment and a model solution for the same assignment. Please grade the submission based on the model solution. Please first analyse each question in the submission and model solution and then grade the submission, giving points for each question based on the model solution. Consider that a different valid solution may exist for the same question. Be generous when grading.
In the very end, summarize the points for each question and the total points for the submission in json format.

Here is a structure hint for the assignment and points:
{structural_hint}

As an example, the json format is as follows:
```json
{
  "Exercise 1.1": {
    "i": 3,
    "ii": 4,
    "iii": 1
  },
  "Exercise 1.2": {
    "i": {
      "a": 1,
      "b": 1,
      "c": 2
    },
    "ii": {
      "a": 1,
      "b": 1,
      "c": 2
    }
  },
  "Exercise 1.3": 4,
  "total": 20
}
```
"""
