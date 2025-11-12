package enu.ui.launa.web.workorder;

import ui.UIBase;
import ui.annotaion.UIElement;

/**
 * @author yuxiangfeng
 */

public enum QueryCarPageUI implements UIBase {

    @UIElement(cssSelect = ".app-main")
    main,

    @UIElement(cssSelect = "[placeholder=\"开单：输入车牌号/手机/姓名\"]",parent = "main")
    customerInfo,

    /**
     * 确认弹窗
     */
    @UIElement(cssSelect = ".el-message-box__wrapper")
    confirmPop,

    /**
     * 弹窗中的确认按钮
     */
    @UIElement(cssSelect = ".el-button--small",idx = 1)
    confirmButton,

    /**
     * 弹窗中的取消按钮
     */
    @UIElement(cssSelect = ".el-button--small",idx = 0)
    cancelButton

}
