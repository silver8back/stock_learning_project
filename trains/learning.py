import numpy as np
import tensorflow as tf
import os
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib as mpl
from data.data_utils import DataUtils
from models.stacked_rnn import StackedRnn


class Learning:
    """학습을 시킨다"""

    def __init__(self, params, is_all_corps_model=False, session_file_name='ALL_CORPS'):
        self.params = params
        self.all_corps_model = is_all_corps_model
        self.session_file_name = session_file_name

    def get_session_path(self, corp_code):
        """저장할 세션의 경로 및 파일명"""
        if self.all_corps_model:
            file_name = self.session_file_name
        else:
            file_name = DataUtils.to_string_corp_code(corp_code)
        return "./data/files/sessions/" + file_name + ".ckpt"

    def draw_plot(self, rmse_vals, test_predict, invest_predicts, comp_name, data_params):
        testY = data_params['testY']
        investY = data_params['investY']
        y = np.append(testY, investY)
        predict = np.append(test_predict, invest_predicts)

        mpl.rcParams['axes.unicode_minus'] = False
        font_name = fm.FontProperties(fname=self.params['kor_font_path'], size=50).get_name()
        plt.rc('font', family=font_name)

        plt.figure(1)
        plt.plot(rmse_vals, 'gold')
        plt.xlabel('Epoch')
        plt.ylabel('Root Mean Square Error')
        plt.title(comp_name)

        plt.figure(2)
        plt.plot(y, 'b')
        plt.plot(predict, 'r')
        plt.xlabel('Time Period')
        plt.ylabel('Stock Price')
        plt.title(comp_name)
        plt.show()

    def save_learning_image(self, sess, saver, comp_code):
        file_path = self.get_session_path(comp_code)
        saver.save(sess, file_path)

    def let_training(self, graph_params, comp_code, data_params):
        """학습을 시킨다."""
        X = graph_params['X']
        Y = graph_params['Y']
        output_keep_prob = graph_params['output_keep_prob']
        train = graph_params['train']
        loss = graph_params['loss']
        trainX = data_params['trainX']
        trainY = data_params['trainY']
        testX = data_params['testX']
        testY = data_params['testY']
        trainCloses = data_params['trainCloses']
        testCloses = data_params['testCloses']

        Y_pred = graph_params['Y_pred']
        targets = graph_params['targets']
        rmse = graph_params['rmse']
        predictions = graph_params['predictions']
        X_closes = graph_params['X_closes']
        loss_up_count = self.params['loss_up_count']
        dropout_keep = self.params['dropout_keep']
        iterations = self.params['iterations']
        rmse_max = self.params['rmse_max']

        saver = tf.train.Saver()
        session_path = self.get_session_path(comp_code)
        restored = False

        with tf.Session() as sess:
            init = tf.global_variables_initializer()
            sess.run(init)

            if os.path.isfile(session_path + '.index'):
                saver.restore(sess, session_path)
                iterations[0] = 0
                restored = True

            # Training step
            min_rmse_val = 999999
            less_cnt = 0
            train_count = 0
            rmse_vals = []

            for i in range(iterations[1]):
                if not restored or i != 0:
                    _, step_loss = sess.run([train, loss], feed_dict={X: trainX, Y: trainY, X_closes: trainCloses,
                                                                      output_keep_prob: dropout_keep})
                test_predict = sess.run(Y_pred, feed_dict={X: testX, output_keep_prob: 1.0})
                rmse_val = sess.run(rmse, feed_dict={targets: testY, predictions: test_predict, X_closes: testCloses})
                rmse_vals.append(rmse_val)

                if i == 0 and restored:
                    max_test_predict, min_rmse_val, = test_predict, rmse_val

                if rmse_val < min_rmse_val:
                    self.save_learning_image(sess, saver, comp_code)
                    less_cnt = 0
                    train_count = i
                    max_test_predict, min_rmse_val, = test_predict, rmse_val
                else:
                    less_cnt += 1
                if i >= iterations[0] and less_cnt > loss_up_count and rmse_max > min_rmse_val:
                    break
            # draw_plot(rmse_vals, max_test_predict, testY, comp_name)
            return min_rmse_val, train_count, rmse_vals, max_test_predict

    def let_learning(self, comp_code, data_params):
        """그래프를 그리고 학습을 시킨다."""
        stacked_rnn = StackedRnn(self.params)
        graph_params = stacked_rnn.get_stacted_rnn_model()
        return self.let_training(graph_params, comp_code, data_params)
