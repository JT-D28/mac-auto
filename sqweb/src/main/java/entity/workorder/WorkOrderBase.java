package entity.workorder;

import lombok.Data;
import java.util.List;

/**
 * @author yuxiangfeng
 */
@Data
public class WorkOrderBase {
    /**
     * 项目名称
     */
    private String itemName;
    /**
     * 项目类型TAB序号
     */
    private int itemTypeTabIndex = 0;
    /**
     * 列表第N个项目
     */
    private int itemIndex = -1;
    /**
     * 第N个施工人员
     */
    private List<Integer> builderIndexList;
    private List<String> achBuilderList;
    /**
     * 第N个销售人员
     */
    private List<Integer> partSaleIndexList;
    private List<String> achSaleList;
    /**
     * 工时
     */
    private String workingHours;
    /**
     * 项目售价
     */
    private String itemPrice;
    /**
     * 项目折扣
     */
    private String itemDiscount;
    /**
     * 项目备注
     */
    private String itemDesc;
    /**
     * 项目下的配件列表
     */
    private List<WorkOrderPartsBase> workOrderPartsList;

}
