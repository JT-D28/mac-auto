package entity.workorder;

import com.yuanpin.shared.entity.base.BaseEntity;
import lombok.Data;
import lombok.EqualsAndHashCode;

import java.math.BigDecimal;
import java.util.Date;

/**
 * @author yuxiangfeng
 */
@EqualsAndHashCode(callSuper = false)
@Data
public class WorkOrder extends BaseEntity {

    private Long customerId;
    private Long carId;
    private String carInfo;
    private String customerInfo;
    private String carNo;
    private Integer carMileage;
    private Long shopId;
    private Long whId;
    private Long salesId;
    private String orderSn;
    private String workType;
    private String workStatus;
    private String payStatus;
    private String payId;
    private String beDebt;
    private String debtStatus;
    private String contactName;
    private String contactMobile;
    private BigDecimal baseAmount;
    private BigDecimal totalAmount;
    private BigDecimal damageAmount;
    private BigDecimal discountFee;
    private BigDecimal cashCard;
    private BigDecimal cardDiscountFee;
    private BigDecimal forceDiscountFee;
    private BigDecimal itemAmount;
    private BigDecimal partsAmount;
    private String discountInfo;
    private String desc;
    private String payDesc;
    private String img;
    private Integer carKeyNum;
    private Date carNextMaintainTime;
    private Integer carNextMaintainMileage;
    private String remark;
    private int evaluateTimes;
    private Long activityId;
    private String orderOrigin;
    private BigDecimal activityDiscountFee;
    private String faultDesc;
    private String beUpload;
    private String uploadState;
    private Long fleetId;
    private String fleetInfo;
    private Long fromWoId;
    private Long newWoId;
}
