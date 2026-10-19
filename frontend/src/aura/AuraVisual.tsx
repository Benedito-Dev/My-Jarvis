export function AuraVisual() {
  return (
    <div className="aura-visual" aria-hidden="true">
      <svg className="aura-visual__svg" viewBox="0 0 1100 800" fill="none" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient id="seda" x1="170" y1="170" x2="930" y2="655" gradientUnits="userSpaceOnUse">
            <stop stopColor="#E5FFFF" stopOpacity=".08" />
            <stop offset=".24" stopColor="#B9FFFF" stopOpacity=".92" />
            <stop offset=".43" stopColor="#4BDDE4" stopOpacity=".38" />
            <stop offset=".61" stopColor="#F3FFFF" stopOpacity=".88" />
            <stop offset=".79" stopColor="#39D9E2" stopOpacity=".34" />
            <stop offset="1" stopColor="#DDFEFF" stopOpacity=".76" />
          </linearGradient>
          <linearGradient id="fio-prata" x1="245" y1="120" x2="864" y2="705" gradientUnits="userSpaceOnUse">
            <stop stopColor="#FFFFFF" stopOpacity=".06" />
            <stop offset=".2" stopColor="#F1FFFF" stopOpacity=".92" />
            <stop offset=".38" stopColor="#67F0F2" stopOpacity=".55" />
            <stop offset=".54" stopColor="#FFFFFF" stopOpacity=".92" />
            <stop offset=".74" stopColor="#7CE9EC" stopOpacity=".34" />
            <stop offset="1" stopColor="#E7FFFF" stopOpacity=".72" />
          </linearGradient>
          <radialGradient id="poeira" cx="0" cy="0" r="1" gradientTransform="translate(610 365) rotate(90) scale(330 370)" gradientUnits="userSpaceOnUse">
            <stop stopColor="#60EAF0" stopOpacity=".16" />
            <stop offset="1" stopColor="#60EAF0" stopOpacity="0" />
          </radialGradient>
          <filter id="brilho-suave" x="-30%" y="-30%" width="160%" height="160%" colorInterpolationFilters="sRGB">
            <feGaussianBlur stdDeviation="15" />
          </filter>
          <filter id="brilho-fino" x="-20%" y="-20%" width="140%" height="140%" colorInterpolationFilters="sRGB">
            <feGaussianBlur stdDeviation="3" />
          </filter>
        </defs>

        <ellipse cx="604" cy="386" rx="375" ry="330" fill="url(#poeira)" />

        <g className="aura-visual__fluxo aura-visual__fluxo--lento">
          <path d="M208 291C319 99 512 66 659 155C821 253 788 409 633 427C467 447 332 262 435 178C553 82 804 187 857 350C911 516 735 682 568 648C407 616 311 457 414 360C518 262 733 322 821 457" stroke="#45E6EC" strokeOpacity=".48" strokeWidth="102" strokeLinecap="round" filter="url(#brilho-suave)" />
          <path d="M208 291C319 99 512 66 659 155C821 253 788 409 633 427C467 447 332 262 435 178C553 82 804 187 857 350C911 516 735 682 568 648C407 616 311 457 414 360C518 262 733 322 821 457" stroke="url(#seda)" strokeOpacity=".33" strokeWidth="74" strokeLinecap="round" />
          <path d="M208 291C319 99 512 66 659 155C821 253 788 409 633 427C467 447 332 262 435 178C553 82 804 187 857 350C911 516 735 682 568 648C407 616 311 457 414 360C518 262 733 322 821 457" stroke="url(#fio-prata)" strokeOpacity=".72" strokeWidth="3" strokeLinecap="round" />
        </g>

        <g className="aura-visual__fluxo aura-visual__fluxo--contrario">
          <path d="M307 536C188 399 253 206 405 143C553 82 732 162 731 286C730 419 544 512 422 426C303 342 367 209 515 207C664 204 853 344 837 485C819 646 614 721 465 650C318 579 298 425 410 337C530 244 726 292 826 379" stroke="url(#seda)" strokeOpacity=".19" strokeWidth="48" strokeLinecap="round" />
          <path d="M307 536C188 399 253 206 405 143C553 82 732 162 731 286C730 419 544 512 422 426C303 342 367 209 515 207C664 204 853 344 837 485C819 646 614 721 465 650C318 579 298 425 410 337C530 244 726 292 826 379" stroke="url(#fio-prata)" strokeOpacity=".8" strokeWidth="2" strokeLinecap="round" />
        </g>

        <g className="aura-visual__fios" stroke="url(#fio-prata)" strokeLinecap="round">
          <path d="M243 325C346 173 440 88 574 112C733 140 863 286 795 386C714 507 485 421 413 309C342 198 448 151 565 179C712 216 865 400 781 550C704 687 507 698 398 577" strokeOpacity=".68" strokeWidth="1.5" />
          <path d="M270 450C326 283 497 185 640 242C791 301 808 451 675 486C541 521 403 410 465 326C526 244 673 305 727 399C787 505 712 602 603 604C493 605 374 532 337 438" strokeOpacity=".52" strokeWidth="1" />
          <path d="M354 604C279 496 310 359 434 276C559 193 740 225 810 321" strokeOpacity=".46" strokeWidth="2" />
          <path d="M433 109C570 63 743 127 842 245C926 344 881 485 801 546" strokeOpacity=".48" strokeWidth="1" />
        </g>

        <g className="aura-visual__pontos">
          <circle cx="278" cy="277" r="2.2" fill="#C8FFFF" />
          <circle cx="324" cy="196" r="1.4" fill="#E9FFFF" />
          <circle cx="387" cy="148" r="2.1" fill="#6CECF0" />
          <circle cx="470" cy="107" r="1.5" fill="#D5FFFF" />
          <circle cx="550" cy="135" r="2.4" fill="#F5FFFF" />
          <circle cx="695" cy="177" r="1.7" fill="#95F9FA" />
          <circle cx="785" cy="257" r="2" fill="#E5FFFF" />
          <circle cx="882" cy="360" r="1.5" fill="#A1F9FB" />
          <circle cx="822" cy="477" r="2.5" fill="#ECFFFF" />
          <circle cx="763" cy="581" r="1.7" fill="#6DE5E9" />
          <circle cx="649" cy="659" r="2" fill="#D6FFFF" />
          <circle cx="514" cy="629" r="1.4" fill="#FFFFFF" />
          <circle cx="411" cy="539" r="2.2" fill="#7DF0F1" />
          <circle cx="368" cy="420" r="1.5" fill="#E9FFFF" />
          <circle cx="602" cy="280" r="2.8" fill="#C3FFFF" filter="url(#brilho-fino)" />
          <circle cx="575" cy="280" r="1.8" fill="#FFFFFF" />
          <circle cx="626" cy="483" r="1.9" fill="#B9FFFF" />
          <circle cx="711" cy="369" r="1.6" fill="#E8FFFF" />
        </g>
      </svg>
    </div>
  );
}
