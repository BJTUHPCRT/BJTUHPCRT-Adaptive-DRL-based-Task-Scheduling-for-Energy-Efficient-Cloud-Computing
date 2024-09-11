"""
   environment is  simulating the datacenter,also as the DRL environment.
"""
from loadDataset import smalltest
from entities import machine
from entities import task
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import math
import time
import logging
class environment:
    def __init__(self, end='no_new_task'):
        #job and machine are lists
        # self.job = job
        # self.machine = machine
        #self.schedulingPolicy = schedulingPolicy
        self.tasks = []
        self.task_reset = []
        self.current_task = None
        self.task_number = 0
        self.machines = []
        self.machines_reset = []
        self.action_len = 0
        self.state_len = 0
        self.total_power = []
        self.total_job_latency = []
        self.total_job_waitingTime = []
        self.reward = []
        self.theta = 0.3 #trade-off of power and job latncy
        #self.task_allocated
        self.task_allocate_counter = 0
        self.unchange_task_number = 0 
        self.detection_list = []
        self.delaytime_sum = 0
        self.detection_number = 0
        self.stage_total_task_cpu = 0
        self.average_task_cpu = 0
        self.change_task_number = 0
        #self.machine_available

        self.action_space = []

        #initialize system
        task_events, machine_events = smalltest.test_workload()
        tt = task_events[0, :]
        for i in range(len(task_events)):
            if not math.isnan(task_events[i, 9]):
                self.tasks.append(task.Task(task_events[i, :]))
            else:
                continue
       
        self.task_number = len(self.tasks)
        self.tasks.sort(key=lambda x: x.timestamp, reverse=False)  #workload
        self.task_reset = self.tasks

        machine_CPUCapcity = [0.1, 0.2, 0.25, 0.3, 1, 0.4, 0.5, 0.5, 0.55, 0.6,
                              0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1, 0.25, 0.5,
                              0.1, 0.25, 1, 0.8, 0.4, 0.9, 0.2, 0.8, 1, 0.7, 0.25]
        for i in range(30):
            machine_temp = machine.Machine(machine_events[i, :])
            machine_temp.machineID = i
            machine_temp.CPUCapacity = machine_CPUCapcity[i]
            self.machines.append(machine_temp)
            self.machines_reset.append(machine_temp)
            self.action_space.append(machine_temp.machineID)
        #self.machines_reset = self.machines
        self.action_len = len(self.action_space)


    def observe(self, task_new):
    
        self.current_task = task_new
        observation = np.zeros((1, self.action_len * 2 + 1)) #dtype=tf.float32
        if task_new is None:
            observation[0, 0] = 0.0
        else:
            observation[0, 0] = task_new.CPURequest
            logging.basicConfig(filename='fjioan.log', level=logging.DEBUG)
            logging.info('task cpu request:')
            logging.info(task_new.CPURequest)
            # print("task cpu request:", task_new.CPURequest)
        #print(observation[0,0])
        count = len(self.machines)
        Index = 1
        for i in range(count):
            observation[0, Index] = self.machines[i].availableCPU
            observation[0, Index+1] = self.machines[i].taskNumber
            Index += 2
        # observation[0, 19] = self.machines[9].availableCPU
        self.state_len = len(observation)
        return observation

    def step(self,action):
  
        power = 0
        job_latency = 0
        done = False
        detection = False
        workload_changed = False
        fluction_index = -1

        current_task = self.current_task
        #we should judge if the task queue is empty
        if current_task != None:
            self.machines[action].allocate_task(current_task)
        next_task = None
        if self.task_allocate_counter == self.task_number:
            done = True
        else:
            next_task, detection = self.get_new_task()  

        #pretrain
        if self.task_allocate_counter == 101 or self.task_allocate_counter==301 or self.task_allocate_counter==401 or self.task_allocate_counter==521\
                or self.task_allocate_counter == 601 or self.task_allocate_counter==701 or self.task_allocate_counter==801 or self.task_allocate_counter == 901\
                or self.task_allocate_counter==997\
                or self.task_allocate_counter==1102 or self.task_allocate_counter==1202 or self.task_allocate_counter==1300 or self.task_allocate_counter== 1400\
                or self.task_allocate_counter==1500 or self.task_allocate_counter==1615 or self.task_allocate_counter==1705 or self.task_allocate_counter==1806\
                or self.task_allocate_counter==1901 or self.task_allocate_counter==1997 or self.task_allocate_counter==2100 or self.task_allocate_counter==2197\
                or self.task_allocate_counter==2300 or self.task_allocate_counter==2412 or self.task_allocate_counter==2500 or self.task_allocate_counter==2716\
                or self.task_allocate_counter==2806 or self.task_allocate_counter==2906:

    
            workload_changed = True

            end = len(self.detection_list) - 1
            # chang, change_index = self.Pettitt_change_point_detection(self.detection_list)
            # f1 = self.standerd_rewards(self.detection_list[0 : change_index])
            f1 = self.standerd_rewards(self.detection_list[1:70])
            f2 = self.detection_list[end]
            # f2 = self.standerd_rewards(self.detection_list[change_index : (end-1)])
            fluction = abs(f1 - f2)
            # print(self.task_allocate_counter,f1,f2)

            #要大于gamma的种类个数，因为大小跟幅度成正比，所以
            if fluction > 0 and fluction <= 0.01:
                fluction_index = 0
            elif fluction > 0.01 and fluction <= 0.015:
                fluction_index = 1
            elif fluction > 0.015 and fluction <= 0.02:
                fluction_index = 2
            elif fluction >= 0.02 and fluction < 0.025:
                fluction_index = 3
            elif fluction >= 0.025 and fluction < 0.03:
                fluction_index = 4
            elif fluction >= 0.03 and fluction < 0.04:
                fluction_index = 5
            elif fluction >= 0.05 and fluction < 0.06:
                fluction_index = 6
            elif fluction >= 0.06 and fluction < 0.1:
                fluction_index = 7
            elif fluction >= 0.1 and fluction < 0.15:
                fluction_index = 8
            elif fluction >= 0.15 and fluction < 0.2:
                fluction_index = 9
            elif fluction >= 0.2 and fluction < 0.25:
                fluction_index = 10
            elif fluction >= 0.25 and fluction < 0.3:
                fluction_index = 11
            elif fluction >= 0.3 and fluction < 0.4:
                fluction_index = 12
            elif fluction >= 0.4 and fluction < 0.5:
                fluction_index = 13
            else:
                fluction_index = 14

           
            self.detection_list = []
        

        reward = self.get_reward()
        self.reward.append(reward)

        for i in range(len(self.machines)):
            power += self.machines[i].idlePower + self.machines[i].activePower * self.machines[i].utilization
        self.total_power.append(power)

        for i in range(len(self.machines)):
            for j in range(len(self.machines[i].running_task)):
                job_latency += 1

            for k in range(len(self.machines[i].waiting_task)):
                job_latency += 1
        self.total_job_latency.append(job_latency)

        return self.observe(next_task), reward, done, workload_changed, fluction_index  #第一个和最后一个task的记录应不应该存储？？

    def temp_step(self,action,temp_task):
      
        power = 0
        job_latency = 0

       
        current_task = self.current_task
        # we should judge if the task queue is empty
        if current_task != None:
            self.machines[action].allocate_task(current_task)
        # next_task = None
        next_task = temp_task 

        reward = self.get_reward()
        self.reward.append(reward)

        for i in range(len(self.machines)):
            power += self.machines[i].idlePower + self.machines[i].activePower * self.machines[i].utilization
        self.total_power.append(power)

      
        for i in range(len(self.machines)):
            for j in range(len(self.machines[i].running_task)):
                job_latency += 1

            for k in range(len(self.machines[i].waiting_task)):
                job_latency += 1
        self.total_job_latency.append(job_latency)

        return self.observe(next_task), reward  

    def create_taskWave(self):
        workload_list = []
        workload_task_list = []
        detection = False

        timeWindow = 10000
        tasks = []
        done = False
        for i in range(self.task_number):
            get_task, delay_time = self.get_new_task()
            if delay_time[0] <= timeWindow and done==False:
                tasks.append(get_task)
                timeWindow = timeWindow - delay_time[0]
            else:
                break

        workload_list = self.compute_cpu_workload(tasks)

        if task != None:
            self.detection_list.append(task.CPURequest)

        if self.task_allocate_counter == self.task_number:
            done = True

        return tasks, done, workload_task_list

    def compute_cpu_workload(self,task_event):

        interval = 60000000  # 间隔5min 300000000
        workload_list = []
        workload_list_tmp = []
        workload_task_list = []
        task_list_tmp = []
        cpu_list = []
        tmp_counter = 0
        done = False
        task_number = 0
        print(len(task_event))
        print(task_event[len(task_event) - 1].timestamp)
        task_list_end = task_event[len(task_event) - 1].timestamp
        k = 0

        start = task_event[0].timestamp
        end = start + interval

        co = int(task_list_end / interval) + 1

        for k in range(0, 1000000):
            total_internal_workload = 0

          
            while task_event[tmp_counter].timestamp < end:
    
                if end > task_list_end:
                    while end < task_list_end:
                        total_internal_workload += task_event[tmp_counter].CPURequest
                        cpu_list.append(task_event[tmp_counter].CPURequest)
                        tmp_counter += 1
                    done = True
                    # printWeekDataset_tmp(workload_list_tmp, str(tmp_counter), day)
                    break
                else:
                    # if not math.isnan(task_event[k].astype(np.int)):
                    total_internal_workload += task_event[tmp_counter].CPURequest
                    cpu_list.append(task_event[tmp_counter].CPURequest)
                    tmp_counter += 1

                task_list_tmp.append(task_event[tmp_counter])

            task_number += 1
           
            workload_task_list.append(task_list_tmp)
            workload_list_tmp.append(total_internal_workload)
            
            workload_list.append(total_internal_workload)
            start = end
            end = start + interval
            if done: break
        # printWeekDataset(task_event,day,week)
        return workload_list, workload_task_list

    def detecte_change(self, neww_task):
        change = False
       
        self.detection_list.append(neww_task)
        change = self.Pettitt_change_point_detection(self.detection_list)
        return  change

    def Pettitt_change_point_detection(self, inputdata):
        change = False
        inputdata = np.array(inputdata)
        n = inputdata.shape[0]
        k = range(n)
        inputdataT = pd.Series(inputdata)
        r = inputdataT.rank()
        Uk = [2 * np.sum(r[0:x]) - x * (n + 1) for x in k]
        Uka = list(np.abs(Uk))
        U = np.max(Uka)
        K = Uka.index(U)
        pvalue = 2 * np.exp((-6 * (U ** 2)) / (n ** 3 + n ** 2))
        if pvalue <= 0.05:
            change_point_desc = '显著'
            change = True
        else:
            change_point_desc = '不显著'
        Pettitt_result = {'突变点位置': K, '突变程度': change_point_desc}
        # return K, Pettitt_result
        return change, K

    def standerd_rewards(self, reward):
        average_r = 0
        for i in range(len(reward)):
            average_r += reward[i]
        average_r = average_r / len(reward)

        return average_r

    def get_new_task(self):
        detection = False
       
        delaytime = np.random.poisson(2, 1) / 10
        time.sleep(delaytime)

        self.delaytime_sum += delaytime[0]
        if self.delaytime_sum >= 50:
            detection = True
            self.delaytime_sum = 0

        task = None
        if self.task_allocate_counter < self.task_number:
            task = self.tasks[self.task_allocate_counter]
            self.task_allocate_counter += 1
            #self.tasks.remove(task)
        else:
            self.task_allocate_counter = 0

        self.detection_list.append(task.CPURequest)
        return task, detection

    def get_reward(self):
        reward = 0
        total_power = 0
        job_latency = 0
        current_job_waiting_time = 0
       
        for i in range(len(self.machines)):
            total_power += self.machines[i].idlePower + self.machines[i].activePower * self.machines[i].utilization
        
        for i in range(len(self.machines)):
            if self.current_task in self.machines[i].running_task :
                for j in range(len(self.machines[i].running_task)):
                    if self.machines[i].running_task[j] is not None:
                        time_remaining = (self.machines[i].running_task[j].executeTime - (self.machines[i].time_horizon - self.machines[i].running_task[j].startTime))
                    else:
                        time_remaining = 0
                    current_job_waiting_time += time_remaining
            if self.current_task in self.machines[i].waiting_task :
                for j in range(len(self.machines[i].running_task)):
                    if self.machines[i].running_task[j] is not None:
                        time_remaining = (self.machines[i].running_task[j].executeTime - (self.machines[i].time_horizon - self.machines[i].running_task[j].startTime))
                    else:
                        time_remaining = 0
                    current_job_waiting_time += time_remaining
                for k in range(len(self.machines[i].waiting_task)):
                    if self.machines[i].waiting_task[k] is not None:
                        time_remaining = self.machines[i].waiting_task[k].executeTime
                    else:
                        time_remaining = 0
                    current_job_waiting_time += time_remaining

        reward = self.theta * total_power + (1 - self.theta) * current_job_waiting_time
        self.total_job_waitingTime.append(current_job_waiting_time)
        # reward += current_job_waiting_time
        return reward

    def reset(self):
        self.task_allocate_counter = 0
        self.tasks = self.task_reset
        self.machines = self.machines_reset
        self.reward = []

        self.unchange_task_number = 0 
        self.delaytime_sum = 0
        self.detection_number = 0
        self.stage_total_task_cpu = 0
        self.average_task_cpu = 0

        for i in range(len(self.machines)):
            self.machines[i].running_task = []
            self.machines[i].waiting_task = []
            self.machines[i].utilization = 0.0
            self.machines[i].availableCPU = self.machines[i].CPUCapacity
