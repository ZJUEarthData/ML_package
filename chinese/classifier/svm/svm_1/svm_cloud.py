from sklearn import svm
import pandas as pd
from sklearn.model_selection import GridSearchCV,ParameterGrid
from sklearn.base import clone
from sklearn.cluster import AffinityPropagation
from sklearn import metrics
import numpy as np
import joblib
import datetime
import sys
import matplotlib.pyplot as plt
import xlwt
from sklearn.model_selection import learning_curve

def para_input(FEATURE_FILE_PATH):
    para = pd.read_excel(FEATURE_FILE_PATH, header=None, dtype='object')
    dic = para.set_index(0).T.to_dict('list')
    for i in dic:
        dic[i] = [x for x in dic[i] if x == x]
    return dic

def write_wrong_label(classifier, data_list, label_list,filename):                # 输出错误分类样本
    predict_label_list = classifier.predict(data_list)
    j = 0
    wrong_file = xlwt.Workbook(encoding = 'utf-8')
    wrong_sheet = wrong_file.add_sheet(u'sheet1', cell_overwrite_ok = True)

    for i in range(len(data_list)):
        if predict_label_list[i] != label_list[i]:
            j = j + 1
            wrong_sheet.write(j, 0, i+1)

    wrong_sheet.write(0, 0, '总分类错误数')
    wrong_sheet.write(0, 1, j)
    wrong_file.save(filename+"wrong.xlsx")

def SVMGridsearch(dmodel, data, labels, param_dict):
    """
    dmodel: 默认模型
    data：训练数据
    labels: 真实分类
    param_dict: 超参数组合字典
    """
    output_models = []

    # create parameter grid
    # 构建超参数网格
    param_grid = ParameterGrid(param_dict)

    # change the parameter attributes in dbscan according to the param_grid
    # 依据网格超参数修改dbscan object 的对应参数，训练模型，得出输出数据
    for param in param_grid:
        for key, value in param.items():
            setattr(dmodel, key, value)

        dmodel.fit(data,labels)
        model = clone(dmodel)
        output_models.append(model)
    # 如果有其他需要输出的数据，继续往里面添加就可以
    return (output_models)
def get_marks(estimator, data, labels, name=None):
    """获取评分，有五种需要知道数据集的实际分类信息，有三种不需要，参考readme.txt

    :param estimator: 模型
    :param name: 初始方法
    :param data: 特征数据集
    """
    estimator.fit(data.astype(np.float64),labels)
    res=estimator.predict(data)
    print(30 * '*', name, 30 * '*')
    print("       模型及参数: ", estimator)
    print("Homogeneity Score         (均一性): ", metrics.homogeneity_score(labels, res))
    print("Completeness Score        (完整性): ", metrics.completeness_score(labels, res))
    print("V-Measure Score           (V量): ", metrics.v_measure_score(labels, res))
    print("Adjusted Rand Score       (调整后兰德指数): ", metrics.adjusted_rand_score(labels,res))
    print("Adjusted Mutual Info Score(调整后的共同信息): ", metrics.adjusted_mutual_info_score(labels, res))
    print("Calinski Harabasz Score:  (方差比指数) ", metrics.calinski_harabasz_score(data,res))
    print("Silhouette Score          (轮廓分数): ", metrics.silhouette_score(data,res))

def plot_learning_curve(model,data,labels,OUTPUT_RESULTS):
    train_sizes, train_scores, test_scores = learning_curve(model, data, labels,
                                                            scoring='adjusted_rand_score', cv=5)
    train_scores_mean = np.mean(train_scores, axis=1)  # 将训练得分集合按行的到平均值
    train_scores_std = np.std(train_scores, axis=1)  # 计算训练矩阵的标准方差
    test_scores_mean = np.mean(test_scores, axis=1)
    test_scores_std = np.std(test_scores, axis=1)
    plt.grid()  # 背景设置为网格线

    plt.fill_between(train_sizes, train_scores_mean - train_scores_std, train_scores_mean + train_scores_std, alpha=0.1,
                     color='r')
    # plt.fill_between()函数会把模型准确性的平均值的上下方差的空间里用颜色填充。
    plt.fill_between(train_sizes, test_scores_mean - test_scores_std, test_scores_mean + test_scores_std, alpha=0.1,
                     color='g')
    plt.plot(train_sizes, train_scores_mean, 'o-', color='r', label='Training score')
    # 然后用plt.plot()函数画出模型准确性的平均值
    plt.plot(train_sizes, test_scores_mean, 'o-', color='g', label='Cross_validation score')
    plt.legend(loc='best')  # 显示图例
    # plt.show()
    TIMESTAMP = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S").replace("'", "")
    plt.savefig(OUTPUT_RESULTS + "{}.png".format(TIMESTAMP))

def main():
    FEATURE_FILE_PATH = sys.argv[1]
    DATA_FILE_PATH = sys.argv[2]
    OUTPUT_MODEL = sys.argv[3]
    OUTPUT_RESULTS = sys.argv[4]

    svm_dict = para_input(FEATURE_FILE_PATH)
    df = pd.read_excel(DATA_FILE_PATH)
    data = df.drop('TRUE VALUE', axis=1)
    labels = df['TRUE VALUE']

    model = svm.SVC()
    output = SVMGridsearch(model, data, labels, svm_dict)
    for i in range(len(output)):
        get_marks(output[i], data=data, labels=labels, name="output" + str(i))

    svm_best_model = GridSearchCV(model, svm_dict, cv=5, scoring='adjusted_rand_score', verbose=1, n_jobs=-1)
    svm_result = svm_best_model.fit(data, labels)
    print(svm_result.best_params_)

    # 保存模型
    joblib.dump(svm_best_model.best_estimator_, OUTPUT_MODEL+"test.pkl")

    # 保存参数
    TIMESTAMP = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S").replace("'", "")
    result = pd.DataFrame(svm_result.best_params_, index=['value'])
    result.to_csv(OUTPUT_RESULTS+"{}.csv".format(TIMESTAMP), index=None)

    # 绘制学习曲线
    plot_learning_curve(svm_best_model.best_estimator_, data, labels,OUTPUT_RESULTS)
    #输出预测错误样本
    write_wrong_label(svm_best_model, data, labels, OUTPUT_RESULTS)

if __name__ == "__main__":
    main()