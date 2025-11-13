package entity.shop;

import com.yuanpin.shared.entity.base.BaseEntity;
import lombok.Data;
import lombok.EqualsAndHashCode;

import java.math.BigDecimal;
import java.util.Date;

@EqualsAndHashCode(callSuper = false)
@Data
public class ShopParts extends BaseEntity {

    private Long shopId;
    private String partsName;
    private String partsNickName;
    private BigDecimal partsPrice;
    private BigDecimal partsBasePrice;
    private BigDecimal partsCostPrice;
    private String oeCode;
    private String unit;
    private Integer status;
    private String brandName;
    private String specificationModel;
    private BigDecimal salesNum;
    private Integer catId;
    private BigDecimal taxRate;
    private String sysPartsSn;
    private String remark;
    private String locationCode; // 库位码
    private String origin; //来源
    private String supportDecimal; // 支持小数点
    private Long templateId; // 模板id
    private String floraPrdLine;
    private String suitCar;
    private Long stockWarnValue; // 库存预警值
    private Date lastOrderTime; // 开单创建时间
    private String barCode; //条形码
    private String img;//配件图片

}
