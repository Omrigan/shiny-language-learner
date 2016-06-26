from language_learner_env import secret_settings
import learner

app = learner.App(secret_settings)
app.listen()
