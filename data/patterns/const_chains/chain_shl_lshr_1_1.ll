define i32 @chain_shl_lshr_1_1(i32 %x) {
entry:
  %tmp = shl i32 %x, 1
  %result = lshr i32 %tmp, 1
  ret i32 %result
}
