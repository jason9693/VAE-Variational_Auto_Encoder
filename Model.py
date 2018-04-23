import tensorflow as tf
import tensorflow.contrib.layers as layers
import ModelUtils as mu

class Model:

    #TODO : replace model to CNN

    def __init__(self,labels=None,input_shape = None,dropout=0):
        self.labels =labels
        self.input_dims = input_shape
        self.dropout = dropout

    def encoder(self,X,name='encoder',sess=None):
        print('encoder')
        affine_iter = 0
        with tf.variable_scope(name) and tf.device('/gpu:0'):
            #encoder_x = tf.reshape(X,[1,-1])
            encoder_x = tf.layers.flatten(X)

            h0 = mu.affine(encoder_x,encoder_x.shape[1],2 ** 10,affine_iter)
            affine_iter += 1

            lay1 = tf.reshape(h0, shape=[tf.shape(encoder_x)[0], 32, 32, 1], name="reshape1")

            conv0 = tf.layers.conv2d(
                inputs=lay1,
                filters=8,
                kernel_size=[7, 7],
                strides=[2, 2],
                name="conv0",
                activation=tf.nn.relu,
                padding='same'
            )
            # print('conv0:',conv0.shape)
            pool0 = tf.layers.max_pooling2d(
                inputs=conv0,
                pool_size=2,
                strides=1,
                padding='same',
                name="max_pool0"
            )

            cycle = 6
            conv = pool0
            for i in range(cycle):
                for j in range(i + 3):
                    conv = mu.residual(i, j, conv, self.dropout)

            ap1 = tf.layers.average_pooling2d(
                inputs=conv,
                pool_size=2,
                strides=1,
                padding='valid',
                name="max_pool1"
            )

            ap_flat = tf.layers.flatten(ap1)

            self.fc_layer = mu.affine(ap_flat,ap_flat.shape[1],self.labels * 2,affine_iter)
            self.lay_out = tf.nn.relu(self.fc_layer)

            mean = self.lay_out[:,:self.labels]
            std_dev = 1e-6 + tf.nn.softplus(self.lay_out[:,self.labels:])

        return mean,std_dev


    def decoder(self,Z,name='decoder',sess=None):
        with tf.variable_scope(name) and tf.device('/gpu:0'):
            self.Z = Z
            decoder_w = tf.get_variable(
                "decoder_W",
                shape=[self.labels,self.input_dims[1]],
                dtype=tf.float32,
                initializer=layers.xavier_initializer()
            )
            decoder_b = tf.get_variable(
                "decoder_b",
                shape=[self.input_dims[1]],
                dtype=tf.float32,
                initializer=layers.xavier_initializer()
            )
            self.affined_decoder = tf.matmul(Z, decoder_w) + decoder_b
            self.out = tf.sigmoid(self.affined_decoder)
        return self.out

    def predict_decoder(self,Z,sess):
        return sess.run(self.out,feed_dict = {self.Z:Z})


