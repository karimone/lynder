from lynder.lynda import LyndaTutorial

def test_tutorial_markdown():
    tutorial = LyndaTutorial(link="https://www.lynda.com/Marketing-tutorials/Marketing-Tools-Digital-Marketing/2822427-2.html")
    tutorial_data = tutorial.get_tutorial_data()
    print(tutorial_data.get_markdown())

