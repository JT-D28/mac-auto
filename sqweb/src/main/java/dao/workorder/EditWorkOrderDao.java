package dao.workorder;

import dao.base.BaseDao;
import dao.common.MyBatisRepository;
import entity.workorder.WorkOrder;

/**
 * @author yuxiangfeng
 */
@MyBatisRepository
public interface EditWorkOrderDao extends BaseDao<WorkOrder> {

}
