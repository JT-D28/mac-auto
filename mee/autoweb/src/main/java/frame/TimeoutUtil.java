package frame;

import java.util.concurrent.*;

/**
 * @author yuxiangfeng
 */
public class TimeoutUtil {

    private static ExecutorService executor = Executors.newSingleThreadExecutor();

    public static <T> T process(Callable<T> task, long timeout) {
        if (task == null) {
            throw new RuntimeException("task is null");
        }
        Future<T> futureRet = executor.submit(task);
        try {
            T ret = futureRet.get(timeout, TimeUnit.SECONDS);
            return ret;
        } catch (InterruptedException e) {
            System.out.println("Interrupt Exception" + e);
        } catch (ExecutionException e) {
            System.out.println("Task execute exception" + e);
        } catch (TimeoutException e) {
            System.out.println("TimeoutException" + e);
            if (futureRet != null && futureRet.isCancelled()) {
                futureRet.cancel(true);
            }
        }
        return null;
    }

    public static <T> T process(Callable<T> task, long timeout, int retryCount) {
        int i = 0;
        do {
            T result = process(task,timeout);
            if ( result != null){
                return result;
            }
            i++;
        }while (i<=retryCount);
        throw new RuntimeException("error");
    }
}
