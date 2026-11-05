"""Función de timeseries-cv 0.1.5; atribución y licencia en third_party/timeseries-cv/."""
import numpy as np

def split_train_val_forwardChaining(sequence, numInputs, numOutputs, numJumps):
    """ Returns sets to train and cross-validate a model using forward chaining technique
    
    Parameters:
        sequence (array)  : Full training dataset
        numInputs (int)   : Number of inputs X and Xcv used at each training and validation
        numOutputs (int)  : Number of outputs y and ycv used at each training and validation
        numJumps (int)    : Number of sequence samples to be ignored between (X,y) sets

    Returns:
        X (2D array)    : Array of numInputs arrays used for training
        y (2D array)    : Array of numOutputs arrays used for training
        Xcv (2D array)  : Array of numInputs arrays used for cross-validation
        ycv (2D array)  : Array of numOutputs arrays used for cross-validation
        
    

Fuente: timeseries-cv 0.1.5; licencia original:
MIT License

Copyright (c) 2021 DidierRLopes

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

The MIT License (MIT)

Copyright (c) 2019 Didier Rodrigues Lopes

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
    X, y, Xcv, ycv = (dict(), dict(), dict(), dict())
    j = 2
    while 1:
        start_ix = 0
        end_ix = 0
        startCv_ix = 0
        endCv_ix = 0
        X_it, y_it, Xcv_it, ycv_it = (list(), list(), list(), list())
        i = 0
        while i < j:
            start_ix = numJumps * i
            end_ix = start_ix + numInputs
            seq_x = sequence[start_ix:end_ix]
            X_it.append(seq_x)
            seq_y = sequence[end_ix:end_ix + numOutputs]
            y_it.append(seq_y)
            i += 1
        if end_ix + numInputs + numOutputs > len(sequence):
            break
        startCv_ix = end_ix
        endCv_ix = end_ix + numInputs
        seq_xcv = sequence[startCv_ix:endCv_ix]
        Xcv_it.append(seq_xcv)
        seq_ycv = sequence[endCv_ix:endCv_ix + numOutputs]
        ycv_it.append(seq_ycv)
        X[j - 2] = np.array(X_it)
        y[j - 2] = np.array(y_it)
        Xcv[j - 2] = np.array(Xcv_it)
        ycv[j - 2] = np.array(ycv_it)
        j += 1
    if len(X) == 0 or len(Xcv) == 0:
        print('The sequence provided does not has size enough to populate the return arrays')
    return (X, y, Xcv, ycv)
