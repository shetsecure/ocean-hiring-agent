from interview_manager import InterviewManager

manager = InterviewManager()

# # Create interview
# interview = manager.create_interview("Mohammed", "Data Scientist")
# print(f"Send link: {interview['interview_link']}")

# Get transcript
transcript = manager.get_transcript("4963dd5a-d3a0-4e5b-88f7-34b26ba48dc9", "Mohammed", "Data Scientist")
if transcript['success']:
    manager.save_transcript(transcript)