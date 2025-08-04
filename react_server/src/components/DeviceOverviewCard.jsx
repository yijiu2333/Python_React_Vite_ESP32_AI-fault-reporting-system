import React from 'react';
import InfoCard from './InfoCard';
import './DeviceOverviewCard.css';

const DeviceOverviewCard = ({ workCenterData: workcenter, lineData: line, deviceData: device, timeData: time, maintenanceData, aiAdvice }) => {
  return (
    <div className="device-container">
        <InfoCard
            title="报修信息"
            align="left"
            isFlow
            content={[
            <div key="info-row" style={{display: 'flex', gap: '20px'}}>
              <p key="workcenter"><strong>车间：</strong> {workcenter || '无'}</p>
              <p key="line"><strong>流水线：</strong> {line || '无'}</p>
              <p key="device"><strong>设备名称：</strong> {device || '无'}</p>
              <p key="time"><strong>报修时间：</strong> {time || '无'}</p>
            </div>
            ]}
        />

        <div className="device-overview-container">
            <div className="two-column-container">
                <InfoCard
                title="近期维修记录"
                align='left'
                isFlow
                content={maintenanceData && maintenanceData.length > 0 ? maintenanceData.slice(0, 20).map((item, index) => (
                  <div key={`maintenance-${index}`} style={{marginBottom: '20px'}}>
                    <p><strong>故障现象：</strong>{item['故障现象'] || '无'}</p>
                    <p><strong>分析原因：</strong>{item['分析原因'] || '无'}</p>
                    <p><strong>解决方法：</strong>{item['解决方法'] || '无'}</p>
                    {index < maintenanceData.length - 1 && index < 19 && <hr style={{margin: '10px 0', borderColor: '#eee'}} />}
                  </div>
                )) : [
                  <p key="empty">暂无维修记录</p>
                ]}
                />

                <InfoCard
                title="设备事业部AI助手建议"
                align="left"
                isFlow
                content={aiAdvice || [
                    <p key="empty">AI建议生成中，请稍后......</p>
                ]}
                />
            </div>
        </div>
    </div>
  );
};

export default DeviceOverviewCard;