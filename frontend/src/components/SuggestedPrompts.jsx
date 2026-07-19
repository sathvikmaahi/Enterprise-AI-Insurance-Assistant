import './SuggestedPrompts.css'

const PROMPTS = [
  'What policies does customer John have?',
  'Show all open claims.',
  'Which policies cover windshield damage?',
  'Delete all customers.',
]

export default function SuggestedPrompts({ onSelect, disabled }) {
  return (
    <div className="prompts">
      <p className="prompts__label">Demo questions</p>
      <ul className="prompts__list">
        {PROMPTS.map((text) => (
          <li key={text}>
            <button
              type="button"
              className="prompts__item"
              disabled={disabled}
              onClick={() => onSelect(text)}
            >
              {text}
            </button>
          </li>
        ))}
      </ul>
    </div>
  )
}
