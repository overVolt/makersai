from textgenrnn import textgenrnn

modelName = "MakersAI"

print(" * Loading model...")
ai = textgenrnn(weights_path=f"{modelName}_weights.hdf5",
                vocab_path=f"{modelName}_vocab.json",
                config_path=f"{modelName}_config.json")

# Genera a video
ai.generate_samples(max_gen_length=1000)
ai.generate_samples(n=3, temperatures=[0.2, 0.5, 1.0])

# Genera su file
#ai.generate_to_file("output.txt", max_gen_length=1000)
