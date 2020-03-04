#!/usr/bin/env python
#
# Optimize blocksize of apps/mmm_block.cpp
#
# This is an extremely simplified version meant only for tutorials
#
from __future__ import print_function

import os
import time
import pandas as pd

import adddeps  # fix sys.path

import opentuner
from opentuner import ConfigurationManipulator
from opentuner import IntegerParameter
from opentuner import MeasurementInterface
from opentuner import Result

threads = 50
newratio = 2
Xmx = '256m'


def save_to_history(newRatio, averageElapsed):
    writeLine = ' NewRatio = {0} , Elapsed mean = {1} \n'.format(newRatio, averageElapsed)
    file1 = open("/home/nayananga/Desktop/wos2/history.txt", "a")  # append mode
    file1.write(writeLine)
    file1.close()


class GccFlagsTuner(MeasurementInterface):

    def manipulator(self):
        """
    Define the search space by creating a
    ConfigurationManipulator
    """
        manipulator = ConfigurationManipulator()
        manipulator.add_parameter(
            IntegerParameter('NewRatio', 1, 10))
        return manipulator

    def run(self, desired_result, input, limit):
        """
    Compile and run a given configuration then
    return performance
    """
        newRatio = desired_result.configuration.data['NewRatio']

        print("command line arguments are: \n threads: {0} \n newratio: {1} \n maximum heap size: {2}".format(threads,
                                                                                                              newratio,
                                                                                                              Xmx))

        gcc_cmd = 'docker exec -d merge_container java -Xmx{} -jar -XX:+UnlockDiagnosticVMOptions -XX:+LogCompilation '.format(
            Xmx)
        gcc_cmd += '-XX:NewRatio={} '.format(newRatio)
        gcc_cmd += '-XX:+PrintGCDetails -XX:+PrintGCDateStamps -Xloggc:/mnt/gc{}.log /mnt/merge_sort_service.jar '.format(time.time())

        self.call_program(gcc_cmd)

        print("Prime service up and running...")

        if os.path.exists(
                "/home/nayananga/Desktop/wos2/jmeter/volume/results/results_threads_{0}/results_threads_{0}.jtl".format(
                    threads)):
            os.remove(
                "/home/nayananga/Desktop/wos2/jmeter/volume/results/results_threads_{0}/results_threads_{0}.jtl".format(
                    threads))
            os.remove(
                "/home/nayananga/Desktop/wos2/jmeter/volume/results/results_threads_{0}/results_threads_{0}-measurement.jtl".format(
                    threads))
            os.remove(
                "/home/nayananga/Desktop/wos2/jmeter/volume/results/results_threads_{0}/results_threads_{0}-warmup.jtl".format(
                    threads))

        time.sleep(20)

        print("JMeter test started in container...")

        run_cmd = 'docker exec jmeter_container java -jar /apache-jmeter-5.2.1/bin/ApacheJMeter.jar -n -t /mnt/MergeSortTestPlan.jmx -Jthreads={0} -l /mnt/results/results_threads_{0}/results_threads_{0}.jtl -q /mnt/user.properties '.format(
            threads)

        self.call_program(run_cmd)

        split_cmd = "java -jar /home/nayananga/Desktop/wos2/jtl-splitter-0.4.1-SNAPSHOT.jar -f /home/nayananga/Desktop/wos2/jmeter/volume/results/results_threads_{0}/results_threads_{0}.jtl -s -t 5".format(
            threads)

        self.call_program(split_cmd)

        t1 = pd.read_csv(
            '/home/nayananga/Desktop/wos2/jmeter/volume/results/results_threads_{0}/results_threads_{0}-measurement.jtl'.format(
                threads))

        run_result = t1.elapsed.mean()

        if os.path.exists(
                "/home/nayananga/Desktop/wos2/jmeter/volume/results/results_threads_{0}/results_threads_{0}.jtl".format(
                    threads)):
            os.remove(
                "/home/nayananga/Desktop/wos2/jmeter/volume/results/results_threads_{0}/results_threads_{0}.jtl".format(
                    threads))
            os.remove(
                "/home/nayananga/Desktop/wos2/jmeter/volume/results/results_threads_{0}/results_threads_{0}-measurement.jtl".format(
                    threads))
            os.remove(
                "/home/nayananga/Desktop/wos2/jmeter/volume/results/results_threads_{0}/results_threads_{0}-warmup.jtl".format(
                    threads))

        print("average response time is : {}".format(run_result))

        save_to_history(newRatio, run_result)

        return Result(time=run_result)

    def save_final_config(self, configuration):
        """called at the end of tuning"""
        print("Optimal New Ratio written to mmm_final_config.json:", configuration.data)
        self.manipulator().save_to_file(configuration.data,
                                        'mmm_final_config.json')


if __name__ == '__main__':
    argparser = opentuner.default_argparser()
    GccFlagsTuner.main(argparser.parse_args())
