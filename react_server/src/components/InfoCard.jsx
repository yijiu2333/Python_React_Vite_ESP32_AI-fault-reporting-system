import PropTypes from 'prop-types';
import './InfoCard.css';

export default function InfoCard({ title, align = 'center', content, isFlow = false }) {
  return (
    <div className="info-card">
      <h3 className={`title ${align}`}>{title}</h3>
      <div className={`content ${isFlow ? 'flow-layout' : 'block-layout'}`}>
        {content}
      </div>
    </div>
  );
}

InfoCard.propTypes = {
  title: PropTypes.string.isRequired,
  align: PropTypes.oneOf(['left', 'center', 'right']),
  content: PropTypes.node.isRequired,
  isFlow: PropTypes.bool
};