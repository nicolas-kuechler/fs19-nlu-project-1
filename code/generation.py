'''
Natural Language Understanding

Project 1: Neural Language Model
Task 1: RNN Language Modelling

File used for task 1.2. Functions used to generate sentence endings.

Authors: Nicolas Küchler, Philippe Blatter, Lucas Brunner, Fynn Faber
Date: 17.04.2019
Version: 3
'''
# Standard packages
import numpy as np
import pandas as pd
import tensorflow as tf

# Local modules
from global_variable import SPECIAL, SENTENCE_LENGTH, PATH_CONTINUATION, BATCH_SIZE, PATH_VOCAB
from util import build_vocab_lookup
from dataset import build_continuation_dataset

def generate(word_to_index_table,index_to_word_table, model=None, path_submission=None):
    '''
    Builds a dataset of the sentences that will be extended by our model. Used our model
    to predict sentences of length less or equal than 20. If the <eos> tag occurs
    before the 20th position in the sentence, it cuts off the rest of the sentence.
    Predictions are stored in the respective submission file.

    Arguments:
        - word_to_index_table: vocabulary lookup table that maps words to indices
        - index_to_word_table: vocabulary lookup table that maps indices to words
        - model: Language model that is used for predictions

    '''

    ds_continuation = build_continuation_dataset(PATH_CONTINUATION, vocab=word_to_index_table)
    ds_continuation = ds_continuation.batch(BATCH_SIZE)
    #ds_continuation = ds_continuation.take(2)  # uncomment for demo purposes
    predicted_sentence = []

    print(f'model: {model}')

    # sentence in \[batch_size, sentence_length-1]
    # length in \[batch_size]
    for sentence, length in ds_continuation:
        
        size_batch = sentence.shape[0]

        # if last fraction is less than the batch size, apply zero padding
        if (size_batch != 64):
            sentence = tf.concat([sentence,tf.zeros((BATCH_SIZE-size_batch,sentence.shape[1]),dtype=tf.int64)],axis=0)

        for i in range(21):#21 predictions, because <bos> is first input
            if (i==0):
                logits,state = model.step(sentence[:,i]) # \in [batch_size, vocab_size]
            else:
                logits,state = model.step(sentence[:,i],state)# \in [batch_size, vocab_size]
                
            preds = tf.nn.softmax(logits, name=None)
            preds = tf.argmax(preds, axis=1) # \in [batch_size]

            # both sentence and preds are of type <class 'tensorflow.python.framework.ops.EagerTensor'>

            # add new word to each input sentence
            update_ind = []
            update_val = []
            for j in range(size_batch):
                #figure out which values need to be updated
                #we take prediction, if symbol is <pad> or <eos>. otherwise keep given word
                if(tf.equal(sentence[j,i+1],tf.constant(1,dtype=tf.int64)) or tf.equal(sentence[j,i+1],tf.constant(2,dtype=tf.int64))):
                    update_ind.append(tf.constant([j,i+1]))
                    update_val.append(tf.constant(preds[j]))
            if not (len(update_ind)==0):
                #if there are avlues to be updated, update them
                indices = tf.stack(update_ind)
                updates = tf.stack(update_val)
                sentence = tf.tensor_scatter_nd_update(sentence,indices,updates)

        for i in range(size_batch):

            #print(f'cutting sentence: {i}')

            #slice to get one sentence
            curr_sentence = sentence[i,:].numpy()
            #print(f'current sentence: {curr_sentence}')

            #find position of <eos>
            eos = np.where(curr_sentence==1) # <eos> is has index 1 (hardcoded)

            # if there is an <eos> pad in the sentence, compute the index of the first appearance
            # if no <eos> was predicted, use 20 as an upper bound
            idx = (eos[0])[0]+1 if len(eos[0])>0 else 21

            #take part to <eos> or at most 20 words
            curr_sentence = curr_sentence[1:idx]

            #map predicted sentence to text
            curr_sentence = sentences_to_text(index_to_word_table,curr_sentence)

            predicted_sentence.append(curr_sentence)

    #add spaces between words and write them to file
    f = open(path_submission, 'w')
    for sentence in predicted_sentence:
        f.write(' '.join(sentence))
        f.write('\n')
    f.close()

    return


def sentences_to_text(index_to_word_table, sentence):
    '''
    Transforms a sentence consisting of IDs into a sentence consisting of words.

    Arguments:
        - index_to_word_table: vocabulary lookup table that maps indices to words
        - sentence: input sentence

    Returns:
        - sentence where the IDs of the words are replaced with the actual words (strings)
    '''

    sentence = tf.cast(sentence, dtype=tf.int64)

    result = []
    for idx in sentence:
        result.append(index_to_word_table.lookup(idx).numpy().decode('utf-8'))

    #print(f'result: {result}')
    return result
