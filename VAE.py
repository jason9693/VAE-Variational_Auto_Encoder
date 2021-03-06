import tensorflow as tf
import Model as model
import numpy as np
class VAE:
    def __init__(self,input_shape,batch_size,label_size = 16,learning_rate=1e-2,sess=None , path=None):
        self.labels = label_size
        self.learning_rate = learning_rate
        self.batch_size = batch_size
        self.input_shape = input_shape
        self.shape = [batch_size] + input_shape
        self.model = model.Model(labels=self.labels,input_shape = self.shape)
        self.__build_net__()
        self.sess = sess
        if path == None:
            self.sess.run(tf.group(tf.global_variables_initializer(), tf.local_variables_initializer()))
        else:
            saver = tf.train.Saver()
            saver.restore(self.sess, path)


    def __build_net__(self):
      with tf.variable_scope('vae',reuse=tf.AUTO_REUSE) :
        self.dropout = tf.placeholder(dtype=tf.float16,shape=(),name="dropout")
        self.X = tf.placeholder(dtype=tf.float32,shape=self.shape)
        z_mean, z_std_dev = self.model.encoder(self.X, name="train_encoder")
        self.KLD = tf.reduce_mean(
            0.5 * tf.reduce_sum(
                tf.square(z_std_dev) + tf.square(z_mean) - 1 - tf.log(tf.square(z_std_dev))
                #z_var + tf.square(z_mean) -1 - tf.log(z_var+ 1e-8)
                , axis=1
            ),
            axis=0
        )

        self.Z = tf.placeholder(dtype=tf.float32,shape=[self.X.shape[0].value, self.labels])
        tf.set_random_seed(777)
        dec_z = z_std_dev * tf.random_normal(z_std_dev.shape,0,1,dtype=tf.float32) + z_mean
        self.pred_X = self.model.decoder(self.Z)

        decoded_X =self.model.decoder(dec_z)
        self.likelihood = tf.reduce_mean(
            tf.reduce_sum(
                self.X * tf.log(decoded_X + 1e-8) + (1 - self.X) * (tf.log(1e-8 + (1 - decoded_X)))
                , axis=1
            )
        )
        self.loss = self.KLD - self.likelihood  # reverse sequence for minimize. ( argmax -> argmin )
        self.optim = tf.train.AdamOptimizer(learning_rate=self.learning_rate).minimize(self.loss)

    def train(self,X,dropout=0):
        return self.sess.run([self.optim,self.loss,self.KLD,self.likelihood],
                        feed_dict={
                                   self.X:X,
                                   self.dropout:dropout}
                        )

    def predict(self,Z):
        return self.sess.run(self.pred_X,feed_dict={
            self.Z:Z,self.dropout:0
        })