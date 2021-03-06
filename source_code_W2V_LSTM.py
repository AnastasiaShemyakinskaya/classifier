'''This script loads pre-trained word embeddings (Word2Vec embeddings)
into a frozen Keras Embedding layer, and uses it to
train a text classification model on the 10 News dataset
(classification of newsgroup messages into 10 different categories).
'''

from __future__ import print_function

import os
import codecs
import gensim
import numpy as np
from keras.preprocessing.text import Tokenizer
from keras.preprocessing.sequence import pad_sequences
from keras.utils import to_categorical
from keras.layers import Dense, Embedding
from keras.models import Sequential
from keras.layers.recurrent import LSTM

MAX_SEQUENCE_LENGTH = 1000
MAX_NUM_WORDS = 20000
EMBEDDING_DIM = 300
VALIDATION_SPLIT = 0.2

# first, build index mapping words in the embeddings set
# to their embedding vector

print('Indexing word vectors.')

embeddings_index = {}
word_model = gensim.models.KeyedVectors.load_word2vec_format("W2V_vectors.bin", binary=True)
#word_model = gensim.models.KeyedVectors.load_word2vec_format("MORPHEME_W2V_vectors.bin", binary=True)
model_size = len(word_model.wv.vocab)
for inx in range(model_size):
    word = word_model.wv.index2word[inx]
    embeddings_index[word] = word_model.wv[word]

print('Found %s word vectors.' % len(embeddings_index))

# second, prepare text samples and their labels
print('Processing text dataset')

texts = []  # list of text samples
labels_index = {}  # dictionary mapping label name to numeric id
labels = []  # list of label ids
S = u'абвгдежзийклмнопрстуфхцчшщыъьэюя'
dir_inx = 0
INPUT_DIR = "TEXTS"
#INPUT_DIR = "MORHEME_TEXTS"
for dir in os.listdir(INPUT_DIR):
    labels_index[os.path.dirname(dir)] = dir_inx
    for file in os.listdir(INPUT_DIR + "\\" + dir):
        train_text = ""
        with codecs.open(INPUT_DIR + "\\" + dir + "\\" + file, "r", encoding="utf-8") as input_file:
            for line in input_file:
                line = line.replace("-", " ")
                line = line.replace(u"—", " ")
                line = line.replace(u"–", " ")
                word_list = line.split(" ")
                for word in word_list:
                    new_word = ''
                    letters_list = list(word.lower())
                    for letter in letters_list:
                        if letter in S:
                            new_word += letter
                    new_word = new_word.strip()
                    if (len(new_word) and (new_word in word_model.wv.vocab)):
                        train_text = train_text + new_word + " "

        train_text = train_text.strip()
        if len(train_text):
            texts.append(train_text)
            labels.append(labels_index[os.path.dirname(dir)])
    dir_inx += 1

print('Found %s texts.' % len(texts))

# finally, vectorize the text samples into a 2D integer tensor
tokenizer = Tokenizer(num_words=MAX_NUM_WORDS)
tokenizer.fit_on_texts(texts)
sequences = tokenizer.texts_to_sequences(texts)

word_index = tokenizer.word_index
print('Found %s unique tokens.' % len(word_index))

data = pad_sequences(sequences, maxlen=MAX_SEQUENCE_LENGTH)

labels = to_categorical(np.asarray(labels))
print('Shape of data tensor:', data.shape)
print('Shape of label tensor:', labels.shape)

# split the data into a training set and a validation set
indices = np.arange(data.shape[0])
np.random.shuffle(indices)
data = data[indices]
labels = labels[indices]
num_validation_samples = int(VALIDATION_SPLIT * data.shape[0])

x_train = data[:-num_validation_samples]
y_train = labels[:-num_validation_samples]
x_val = data[-num_validation_samples:]
y_val = labels[-num_validation_samples:]

print('Preparing embedding matrix.')

# prepare embedding matrix
num_words = min(MAX_NUM_WORDS, len(word_index) + 1)
embedding_matrix = np.zeros((num_words, EMBEDDING_DIM))
for word, i in word_index.items():
    if i >= MAX_NUM_WORDS:
        continue
    embedding_vector = embeddings_index.get(word)
    if embedding_vector is not None:
        # words not found in embedding index will be all-zeros.
        embedding_matrix[i] = embedding_vector

# load pre-trained word embeddings into an Embedding layer
# note that we set trainable = False so as to keep the embeddings fixed
embedding_layer = Embedding(num_words,
                            EMBEDDING_DIM,
                            weights=[embedding_matrix],
                            input_length=MAX_SEQUENCE_LENGTH,
                            trainable=False)

print('Training model.')

# train a 1D convnet with global maxpooling
model = Sequential()
model.add(embedding_layer)
model.add(LSTM(128))
model.add(Dense(dir_inx, activation='softmax'))
model.compile(loss='categorical_crossentropy',
              optimizer='rmsprop',
              metrics=['acc'])

model.fit(x_train, y_train,
          batch_size=128,
          epochs=10,
          validation_data=(x_val, y_val))

scores = model.evaluate(x_val, y_val)
print("Точность на тестовых данных: %.2f%%" % (scores[1] * 100))
result = model.predict(x_val)
print(np.argmax(result, axis=1))