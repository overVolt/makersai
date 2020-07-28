from textgenrnn import textgenrnn
from os.path import isfile

print("\n * Loading config...")

model_cfg = {
    'word_level': False,            # set to True if want to train a word-level model (requires more data and smaller max_length)
    'rnn_size': 256,                # number of LSTM cells of each layer (128/256 recommended)
    'rnn_layers': 5,                # number of LSTM layers (>=2 recommended)
    'rnn_bidirectional': False,     # consider text both forwards and backward, can give a training boost
    'max_length': 30,               # number of tokens to consider before predicting the next (20-40 for characters, 5-10 for words recommended)
    'max_words': 10000,             # maximum number of words to model; the rest will be ignored (word-level model only)
    'name': "MakersAI"              # model name
}

train_cfg = {
    'line_delimited': True,         # set to True if each text has its own line in the source file
    'num_epochs': 20,               # set higher to train the model for longer
    'gen_epochs': 5,                # generates sample text from model after given number of epochs
    'num_runs': 5,                  # number of times to repeat the training for
    'train_size': 1.0,              # proportion of input data to train on: setting < 1.0 limits model from learning perfectly
    'dropout': 0.1,                 # ignore a random proportion of source tokens each epoch, allowing model to generalize better
    'validation': False,            # if train__size < 1.0, test on holdout dataset; will make overall training slower
    'is_csv': False,                # set to True if file is a CSV exported from Excel/BigQuery/pandas
    'batch_size': 2048,             # training batch size
    'train_files': 11               # number of files that compose the dataset: dataset/dataN.txt
}

print("\n * Training model...")
for r in range(train_cfg['num_runs']):
    print(f" * Starting run {r+1} of {train_cfg['num_runs']}...")
    for f in range(train_cfg['train_files']):
        filename = f"dataset/data{f+1}.txt"
        print(f" * Training on {filename} for {train_cfg['num_epochs']} epochs...")

        if not isfile(f"{model_cfg['name']}_weights.hdf5"):
            isNewModel = True
            ai = textgenrnn(name=model_cfg['name'])
        else:
            isNewModel = False
            ai = textgenrnn(name=model_cfg['name'],
                            vocab_path=f"{model_cfg['name']}_vocab.json",
                            config_path=f"{model_cfg['name']}_config.json",
                            weights_path=f"{model_cfg['name']}_weights.hdf5")
        train_function = ai.train_from_file if train_cfg['line_delimited'] else ai.train_from_largetext_file

        train_function(
            file_path=filename,
            new_model=isNewModel,
            num_epochs=train_cfg['num_epochs'],
            gen_epochs=train_cfg['gen_epochs'],
            batch_size=train_cfg['batch_size'],
            train_size=train_cfg['train_size'],
            dropout=train_cfg['dropout'],
            validation=train_cfg['validation'],
            is_csv=train_cfg['is_csv'],
            rnn_layers=model_cfg['rnn_layers'],
            rnn_size=model_cfg['rnn_size'],
            rnn_bidirectional=model_cfg['rnn_bidirectional'],
            max_length=model_cfg['max_length'],
            dim_embeddings=100,
            word_level=model_cfg['word_level']
        )

        print("\n * Saving model...")
        ai.save(f"{model_cfg['name']}_backup.hdf5")
