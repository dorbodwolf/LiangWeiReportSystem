from django.shortcuts import render
from django.http import HttpResponse
from  django.template import loader #模板加载函数
from .models import ZengWei, FigureSpot
import time
from django.db.models import Count

def index(request):
    """
    zengwei表分析
    """
    periods = [] #下发图斑年份期数的编号
    count_of_periods = [] #下发期数对应的图斑数量
    for iter in range(len(ZengWei.objects.values("yearperiod").distinct())):
        period = ZengWei.objects.values("yearperiod").distinct()[iter]['yearperiod']
        periods.append(period)
        count = ZengWei.objects.filter(yearperiod = str(period)).count()
        count_of_periods.append(count)
    periods_dict = dict(zip(periods, count_of_periods))
    localtime = time.localtime(time.time()) #返回当前日期
    localtime = time.asctime(localtime) #日期格式化输出
    zengwei_stat_dict, subset_of_nt, subset_of_st = zengwei_stat(periods[0]) # sample_dict = {'文城镇' :[1,2,3,4,5]}
    """
    figurespot表分析
    """
    chuzhi_count = FigureSpot.objects.all().count()
    illegal_count =  FigureSpot.objects.filter(whetherillegal = '是').count()
    legal_count =  FigureSpot.objects.filter(whetherillegal = '否').count()
    xiafa_count =  FigureSpot.objects.filter(figurespotnumber__contains = 'A' ).count()
    zicha_count =  FigureSpot.objects.filter(figurespotnumber__contains = 'B').count()
    chuzhi_town = figurespot_stat(periods)
    """
    context参数内容设置
    """
    context ={
        # zengwei表
        'periods': periods,
        'count_of_periods': count_of_periods,
        'current_time': localtime,
        'periods_dict': periods_dict,
        'zengwei_town': zengwei_stat_dict,
        'luoru_jbnt': subset_of_nt,
        'luoru_sthx': subset_of_st,
        # figurespot表
        'chuzhi_count': chuzhi_count,
        'illegal_count': illegal_count,
        'legal_count': legal_count,
        'xiafa_count': xiafa_count,
        'zicha_count': zicha_count,
        'chuzhi_town': chuzhi_town
    }
    return  render(request, "report/index.html", context)

def zengwei_stat(yearperiod):
    """
    某一期违法建筑的统计信息生成
    param: yearperiod: 期号
    """
    count_of_xzmc = ZengWei.objects.filter(yearperiod=yearperiod).values('xzmc').annotate(count = Count("pk")).order_by('count') #annotate返回的是一个queryset
    jbnt_in_xzmc = ZengWei.objects.filter(yearperiod=yearperiod).exclude(sfjbnt='完全在优化基本农田外').values('xzmc').annotate(Count("pk"))
    lyhx_in_xzmc = ZengWei.objects.filter(yearperiod=yearperiod).exclude(sflyhx='完全在陆域生态红线外').values('xzmc').annotate(Count("pk"))
    zengwei_stat_dict = {}
    for iter in count_of_xzmc:
        town = iter['xzmc']
        count = iter['count']
        count_jbnt = 0
        percent_jbnt = 0
        count_lyhx = 0
        percent_lyhx = 0
        for iter_ in lyhx_in_xzmc:
            if town == iter_['xzmc']:
                count_lyhx = iter_['pk__count']
                percent_lyhx = count_lyhx / count
        for iter_ in jbnt_in_xzmc:
            if town == iter_['xzmc']:
                count_jbnt = iter_['pk__count']
                percent_jbnt = count_jbnt / count
        zengwei_stat_dict.update({town:[count,count_jbnt,percent_jbnt,count_lyhx,percent_lyhx]})
    # 对统计字典按基本农田个数排序
    sort_by_nt = dict(sorted(zengwei_stat_dict.items(), key = lambda v: v[1][1], reverse=True))
    # 提取只包含落入农田的乡镇
    subset_of_nt = {key: value for key, value in sort_by_nt.items() if value[1] > 0}
    # 对统计字典按落入生态红线个数排序
    sort_by_st = dict(sorted(zengwei_stat_dict.items(), key = lambda v: v[1][3], reverse=True))
    # 提取只包含落入农田的乡镇
    subset_of_st = {key: value for key, value in sort_by_st.items() if value[3] > 0}
    return zengwei_stat_dict, subset_of_nt, subset_of_st


# def zengwei_stat_limitcount(yearperiod):
#     """
#     某一期违法建筑的统计信息生成, 只返回按乡镇的统计
#     param: yearperiod: 最新一期的期号
#     """
#     count_of_xzmc = ZengWei.objects.filter(yearperiod=yearperiod).values('xzmc').annotate(count = Count("pk")).order_by('count') #annotate返回的是一个queryse
#     zengwei_stat_dict = {}
#     for iter in count_of_xzmc:
#         town = iter['xzmc']
#         count = iter['count']
#         zengwei_stat_dict.update({town:count})
#     return zengwei_stat_dict

def figurespot_stat(periods):
    """
    摸底调查、计划处置、自查图斑的工作情况统计分析
    parameter periods 期数列表
    """
    # 最近两期的zengwei按乡镇计数
    count_zeng_latest = ZengWei.objects.filter(yearperiod=periods[0]).values('xzmc').annotate(count = Count("pk")) #annotate返回的是一个queryse
    count_zeng_penul =  ZengWei.objects.filter(yearperiod=periods[1]).values('xzmc').annotate(count = Count("pk"))

    # figurespot表的各种图斑类型和图斑状态按乡镇计数
    count_by_xzmc = FigureSpot.objects.values('country').annotate(count = Count("pk")).order_by('country') 
    count_of_zicha = FigureSpot.objects.filter(figurespotnumber__contains = 'B').values('country').annotate(count = Count("pk")).order_by('country') 
    count_of_illegal = FigureSpot.objects.filter(whetherillegal = '是').values('country').annotate(count = Count("pk")).order_by('country') 
    count_of_plan = FigureSpot.objects.filter(figurespotstate = '2').values('country').annotate(count = Count("pk")).order_by('country') 
    count_of_power = FigureSpot.objects.filter(figurespotstate = '3').values('country').annotate(count = Count("pk")).order_by('country') 
    count_of_over = FigureSpot.objects.filter(figurespotstate = '4').values('country').annotate(count = Count("pk")).order_by('country') 

    # 充分利用QuerySet API装载字典
    chuzhi_stat_dict = {}
    for iter in count_by_xzmc:
        zeng_latest = 0
        zeng_penul = 0
        zicha = 0
        illegal = 0
        plan = 0
        power = 0
        over = 0
        if count_zeng_latest.filter(xzmc =  iter['country']).count() > 0:
            zeng_latest = count_zeng_latest.filter(xzmc =  iter['country'])[0]['count']
        if count_zeng_penul.filter(xzmc =  iter['country']).count() > 0:
            zeng_penul = count_zeng_penul.filter(xzmc =  iter['country'])[0]['count']
        if count_of_zicha.filter(country =  iter['country']).count() > 0:
            zicha = count_of_zicha.filter(country =  iter['country'])[0]['count']
        if count_of_illegal.filter(country = iter['country']).count() > 0:
            illegal = count_of_illegal.filter(country = iter['country'])[0]['count']
        if count_of_plan.filter(country = iter['country']).count() > 0:
            plan = count_of_plan.filter(country = iter['country'])[0]['count']
        if count_of_power.filter(country = iter['country']).count() > 0:
            power = count_of_power.filter(country = iter['country'])[0]['count']
        if count_of_over.filter(country = iter['country']).count() > 0:
            over = count_of_over.filter(country = iter['country'])[0]['count']
        town = iter['country']
        count = iter['count']
        chuzhi_stat_dict.update({town:[zeng_latest, zeng_penul, zicha, count, illegal, plan, power, over]})
    return chuzhi_stat_dict